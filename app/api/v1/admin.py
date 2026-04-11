from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
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
    query = db.query(Product).filter(
        Product.is_approved == False, Product.status == ProductStatus.AVAILABLE
    )

    if search:
        search_term = search.strip()
        query = query.filter(
            (Product.title.ilike(f"%{search_term}%"))
            | (Product.description.ilike(f"%{search_term}%"))
        )

    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


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
