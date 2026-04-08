from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

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
)
from app.schemas.schemas import (
    ProductResponse,
    UserResponse,
    AnalyticsResponse,
    RatingResponse,
    TicketResponse,
)
from app.api.v1.notifications import create_notification

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    role: UserRole


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


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

    return {
        "total_users": total_users,
        "total_products": total_products,
        "pending_products": pending_products,
        "approved_products": approved_products,
        "sold_products": sold_products,
        "customers": customers,
        "sellers": sellers,
    }


@router.get("/products/pending", response_model=List[ProductResponse])
def get_pending_products(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    products = (
        db.query(Product)
        .filter(Product.is_approved == False, Product.status == ProductStatus.AVAILABLE)
        .order_by(Product.created_at.desc())
        .all()
    )
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

    return product


@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = (
        db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    )
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
