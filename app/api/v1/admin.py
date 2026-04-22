from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import csv
import io

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import (
    User,
    Product,
    ProductStatus,
    UserRole,
    NotificationType,
    Rating,
    Ticket,
    TicketStatus,
    TicketType,
    Conversation,
    Message,
    ActivityLog,
)
from app.schemas.schemas import (
    ProductResponse,
    UserResponse,
    AnalyticsResponse,
    RatingResponse,
    TicketResponse,
    SendNotificationRequest,
)
from app.api.v1.notifications import create_notification

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    role: UserRole


class BulkActionRequest(BaseModel):
    product_ids: List[int] = Field(..., min_length=1, max_length=50)
    action: str


class SendNotificationRequest(BaseModel):
    user_id: int
    title: str
    message: str


def log_activity(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    details: str = None,
):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    db.commit()


def require_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from sqlalchemy import func
    from app.models.models import Category

    total_users = db.query(User).count()
    total_products = db.query(Product).count()

    pending_products = (
        db.query(Product)
        .filter(Product.is_approved == False, Product.status == ProductStatus.AVAILABLE)
        .count()
    )

    approved_products = (
        db.query(Product)
        .filter(Product.is_approved == True, Product.status == ProductStatus.AVAILABLE)
        .count()
    )

    sold_products = (
        db.query(Product).filter(Product.status == ProductStatus.SOLD).count()
    )

    customers = db.query(User).filter(User.role == UserRole.CUSTOMER).count()

    sellers = db.query(User).filter(User.role == UserRole.SELLER).count()

    activity_today = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.created_at
            >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        )
        .count()
    )

    products_by_category = (
        db.query(Category.name, func.count(Product.id))
        .join(Product, Product.category_id == Category.id, isouter=True)
        .group_by(Category.name)
        .all()
    )

    products_by_category_data = [
        {"name": cat[0] or "Uncategorized", "count": cat[1]}
        for cat in products_by_category
    ]

    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_over_time_data = [
        {"name": role[0].value if role[0] else "unknown", "count": role[1]}
        for role in users_by_role
    ]

    return {
        "total_users": total_users,
        "total_products": total_products,
        "pending_products": pending_products,
        "approved_products": approved_products,
        "sold_products": sold_products,
        "customers": customers,
        "sellers": sellers,
        "activity_today": activity_today,
        "products_by_category": products_by_category_data,
        "users_over_time": users_over_time_data,
    }


@router.get("/export/users.csv")
def export_users_csv(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Phone", "Username", "Role", "Active", "Created At"])

    for user in users:
        writer.writerow(
            [
                user.id,
                user.phone,
                user.username or "",
                user.role.value,
                user.is_active,
                user.created_at.isoformat() if user.created_at else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.get("/export/products.csv")
def export_products_csv(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    products = db.query(Product).order_by(Product.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Title", "Price", "Status", "Approved", "Seller ID", "Created At"]
    )

    for product in products:
        writer.writerow(
            [
                product.id,
                product.title,
                product.price,
                product.status.value,
                product.is_approved,
                product.seller_id,
                product.created_at.isoformat() if product.created_at else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/products/pending", response_model=List[ProductResponse])
def get_pending_products(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        query = db.query(Product).filter(
            Product.is_approved == False, Product.status == ProductStatus.AVAILABLE
        )

        if search:
            search_term = search.strip()
            query = query.filter(
                (Product.title.ilike(f"%{search_term}%"))
                | (Product.description.ilike(f"%{search_term}%"))
            )

        products = (
            query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
        )

        # Convert to dict to avoid validation issues
        return [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "price": p.price,
                "image_url": p.image_url,
                "status": p.status.value
                if hasattr(p.status, "value")
                else str(p.status),
                "is_approved": p.is_approved,
                "is_featured": p.is_featured,
                "seller_id": p.seller_id,
                "category_id": p.category_id,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "sold_at": p.sold_at,
            }
            for p in products
        ]
    except Exception as e:
        print(f"Error in get_pending_products: {e}")
        return []


@router.get("/products", response_model=List[ProductResponse])
def get_all_products(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    status: str = None,
    is_approved: bool = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(Product)

    if search:
        search_term = search.strip()
        query = query.filter(
            (Product.title.ilike(f"%{search_term}%"))
            | (Product.description.ilike(f"%{search_term}%"))
        )

    if status:
        query = query.filter(Product.status == ProductStatus(status))

    if is_approved is not None:
        query = query.filter(Product.is_approved == is_approved)

    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


@router.post("/products/{product_id}/approve", response_model=ProductResponse)
def approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    product.is_approved = True
    db.commit()
    db.refresh(product)

    create_notification(
        db=db,
        user_id=product.seller_id,
        notification_type=NotificationType.PRODUCT_APPROVED,
        title="Product Approved",
        message=f'Your product "{product.title}" has been approved and is now live!',
        related_id=product.id,
    )
    db.commit()

    log_activity(
        db, admin.id, "approve", "product", product.id, f"Approved: {product.title}"
    )

    return product


@router.post("/products/{product_id}/reject", response_model=ProductResponse)
def reject_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    product.status = ProductStatus.ARCHIVED
    product.is_approved = False
    db.commit()
    db.refresh(product)

    create_notification(
        db=db,
        user_id=product.seller_id,
        notification_type=NotificationType.PRODUCT_REJECTED,
        title="Product Rejected",
        message=f'Your product "{product.title}" has been rejected.',
        related_id=product.id,
    )
    db.commit()

    log_activity(
        db, admin.id, "reject", "product", product.id, f"Rejected: {product.title}"
    )

    return product


@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    role: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(User)

    if search:
        search_term = search.strip()
        query = query.filter(
            (User.phone.ilike(f"%{search_term}%"))
            | (User.username.ilike(f"%{search_term}%"))
        )

    if role:
        query = query.filter(User.role == UserRole(role))

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    user.role = new_role
    db.commit()
    return {"message": f"User role updated to {new_role.value}"}


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    user.is_active = not user.is_active
    db.commit()
    status = "deactivated" if not user.is_active else "activated"
    return {"message": f"User {status}"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    db.delete(user)
    db.commit()
    return None


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    db.delete(product)
    db.commit()
    return None


@router.get("/ratings", response_model=List[RatingResponse])
def get_all_ratings(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ratings = (
        db.query(Rating)
        .order_by(Rating.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return ratings


@router.delete("/ratings/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found"
        )

    db.delete(rating)
    db.commit()
    return None


@router.get("/tickets", response_model=List[TicketResponse])
def get_all_tickets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    tickets = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tickets


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    new_status: TicketStatus,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    ticket.status = new_status
    db.commit()
    return {"message": f"Ticket status updated to {new_status.value}"}


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_for_dispute(
    conversation_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_id": m.sender_id,
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/products/bulk")
def bulk_product_action(
    data: BulkActionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    products = db.query(Product).filter(Product.id.in_(data.product_ids)).all()

    approved_count = 0
    rejected_count = 0

    for product in products:
        if data.action == "approve":
            product.is_approved = True
            create_notification(
                db=db,
                user_id=product.seller_id,
                notification_type=NotificationType.PRODUCT_APPROVED,
                title="Product Approved",
                message=f'Your product "{product.title}" has been approved!',
                related_id=product.id,
            )
            approved_count += 1
        elif data.action == "reject":
            product.status = ProductStatus.ARCHIVED
            product.is_approved = False
            create_notification(
                db=db,
                user_id=product.seller_id,
                notification_type=NotificationType.PRODUCT_REJECTED,
                title="Product Rejected",
                message=f'Your product "{product.title}" has been rejected.',
                related_id=product.id,
            )
            rejected_count += 1

    db.commit()

    return {"message": f"Approved {approved_count}, rejected {rejected_count} products"}


@router.post("/notify")
def send_notification(
    data: SendNotificationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    create_notification(
        db=db,
        user_id=data.user_id,
        notification_type=NotificationType.PRODUCT_APPROVED,
        title=data.title,
        message=data.message,
    )
    db.commit()

    log_activity(db, admin.id, "notify", "user", data.user_id, f"Sent: {data.title}")

    return {"message": "Notification sent"}


class BroadcastNotificationRequest(BaseModel):
    title: str
    message: str


@router.post("/notify/broadcast")
def broadcast_notification(
    data: BroadcastNotificationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).all()
    count = 0
    for user in users:
        create_notification(
            db=db,
            user_id=user.id,
            notification_type=NotificationType.PRODUCT_APPROVED,
            title=data.title,
            message=data.message,
        )
        count += 1

    db.commit()

    log_activity(
        db, admin.id, "broadcast", "user", 0, f"Sent to {count} users: {data.title}"
    )

    return {"message": f"Notification sent to {count} users"}


@router.get("/activity-logs")
def get_activity_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/kyc/pending")
def get_pending_kyc(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = (
        db.query(User)
        .filter(User.kyc_status == "submitted")
        .order_by(User.kyc_submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": u.id,
            "phone": u.phone,
            "username": u.username,
            "role": u.role.value,
            "kyc_id_number": u.kyc_id_number,
            "kyc_id_front_url": u.kyc_id_front_url,
            "kyc_selfie_url": u.kyc_selfie_url,
            "kyc_submitted_at": u.kyc_submitted_at.isoformat()
            if u.kyc_submitted_at
            else None,
        }
        for u in users
    ]


@router.post("/kyc/{user_id}/approve")
def approve_kyc(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.kyc_status = "approved"
    user.kyc_reviewed_at = datetime.utcnow()
    db.commit()

    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="KYC Approved",
        message="Your identity verification has been approved. Your account is now fully verified.",
    )

    log_activity(
        db,
        admin.id,
        "approve_kyc",
        "user",
        user_id,
        f"Approved KYC for user {user.username or user.phone}",
    )
    return {"message": "KYC approved"}


@router.post("/kyc/{user_id}/reject")
def reject_kyc(
    user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="KYC review is currently disabled",
    )


@router.post("/users/{user_id}/verify")
def verify_seller(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_identity_verified = True
    db.commit()

    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="Account Verified",
        message="Your account has been verified. You can now post products.",
    )

    log_activity(
        db,
        admin.id,
        "verify_seller",
        "user",
        user_id,
        f"Verified seller account for {user.username or user.phone}",
    )
    return {"message": "Seller verified"}


@router.post("/users/{user_id}/unverify")
def unverify_seller(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_identity_verified = False
    db.commit()

    log_activity(
        db,
        admin.id,
        "unverify_seller",
        "user",
        user_id,
        f"Unverified seller account for {user.username or user.phone}",
    )
    return {"message": "Seller unverified"}


@router.patch("/users/{user_id}/subscription")
def update_subscription(
    user_id: int,
    tier: str,
    duration_days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if tier not in ["free", "basic", "standard", "premium"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tier"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.subscription_tier = tier
    if tier == "free":
        user.subscription_expires_at = None
        user.subscription_started_at = None
        user.featured_listings_used_this_month = 0
    else:
        user.subscription_started_at = datetime.utcnow()
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=duration_days)
    db.commit()

    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="Subscription Updated",
        message=f"Your subscription has been updated to {tier.title()} tier.",
    )

    log_activity(
        db,
        admin.id,
        "update_subscription",
        "user",
        user_id,
        f"Set subscription to {tier} for {duration_days} days",
    )
    return {"message": f"Subscription updated to {tier}"}


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend admin"
        )

    user.is_suspended = True
    user.suspension_reason = reason
    db.commit()

    products = db.query(Product).filter(Product.seller_id == user_id).all()
    for p in products:
        p.is_approved = False

    db.commit()

    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="Account Suspended",
        message=f"Your account has been suspended. Reason: {reason}. Contact support for assistance.",
    )

    log_activity(
        db, admin.id, "suspend_user", "user", user_id, f"Suspended user: {reason}"
    )
    return {"message": "User suspended"}


@router.post("/users/{user_id}/unsuspend")
def unsuspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_suspended = False
    user.suspension_reason = None
    db.commit()

    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="Account Reactivated",
        message="Your account has been reactivated. You now have full access.",
    )

    log_activity(db, admin.id, "unsuspend_user", "user", user_id, "Reactivated user")
    return {"message": "User unsuspended"}


@router.get("/subscriptions")
def get_subscriptions(
    skip: int = 0,
    limit: int = 50,
    tier: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(User).filter(User.role == UserRole.SELLER)

    if tier:
        query = query.filter(User.subscription_tier == tier)

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": u.id,
            "phone": u.phone,
            "username": u.username,
            "subscription_tier": u.subscription_tier,
            "subscription_started_at": u.subscription_started_at.isoformat()
            if u.subscription_started_at
            else None,
            "subscription_expires_at": u.subscription_expires_at.isoformat()
            if u.subscription_expires_at
            else None,
            "featured_listings_used": u.featured_listings_used_this_month or 0,
            "is_verified": u.kyc_status == "approved"
            and u.subscription_tier in ["standard", "premium"],
        }
        for u in users
    ]


@router.get("/reports")
def get_reports(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.models import Report

    query = db.query(Report)

    if status_filter:
        query = query.filter(Report.status == status_filter)

    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": r.id,
            "reporter_id": r.reporter_id,
            "reported_user_id": r.reported_user_id,
            "reported_product_id": r.reported_product_id,
            "reported_conversation_id": r.reported_conversation_id,
            "reason": r.reason,
            "description": r.description,
            "status": r.status,
            "admin_notes": r.admin_notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in reports
    ]


@router.patch("/reports/{report_id}")
def update_report(
    report_id: int,
    status: str,
    admin_notes: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.models import Report

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    report.status = status
    if admin_notes:
        report.admin_notes = admin_notes
    if status in ["resolved", "dismissed"]:
        report.resolved_at = datetime.utcnow()

    db.commit()
    log_activity(
        db,
        admin.id,
        "update_report",
        "report",
        report_id,
        f"Updated status to {status}",
    )
    return {"message": "Report updated"}


@router.post("/migrate")
def run_migration(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Run database migrations for missing columns."""
    from sqlalchemy import text

    migrations = [
        ("users", "is_identity_verified", "BOOLEAN DEFAULT FALSE"),
        ("users", "pending_tier", "VARCHAR(20)"),
        ("users", "pending_payment_checkout_id", "VARCHAR(100)"),
        ("users", "payment_pending_at", "TIMESTAMP WITH TIME ZONE"),
        ("products", "is_featured", "BOOLEAN DEFAULT FALSE"),
        ("products", "featured_until", "TIMESTAMP WITH TIME ZONE"),
        ("products", "featured_by_admin", "BOOLEAN DEFAULT FALSE"),
    ]

    results = []
    for table, column, col_type in migrations:
        try:
            result = db.execute(
                text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            """)
            )
            if result.fetchone() is None:
                db.execute(
                    text(f"""
                    ALTER TABLE {table} ADD COLUMN {column} {col_type}
                """)
                )
                results.append(f"Added {column} to {table}")
            else:
                results.append(f"{column} already exists")
        except Exception as e:
            results.append(f"Error adding {column}: {str(e)}")

    db.commit()
    return {"results": results}
