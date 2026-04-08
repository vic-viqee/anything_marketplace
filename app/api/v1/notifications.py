from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Notification as NotificationModel, NotificationType

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    related_id: int | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notifications = (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": n.id,
            "notification_type": n.notification_type.value,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "related_id": n.related_id,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = (
        db.query(NotificationModel)
        .filter(
            NotificationModel.user_id == current_user.id,
            NotificationModel.is_read == False,
        )
        .count()
    )
    return {"unread_count": count}


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notification = (
        db.query(NotificationModel)
        .filter(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notification.is_read = True
    db.commit()
    return None


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return None


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    related_id: int | None = None,
):
    notification = NotificationModel(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        related_id=related_id,
    )
    db.add(notification)
    return notification
