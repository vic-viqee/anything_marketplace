from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Conversation, Message
from app.schemas.schemas import NudgeResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/nudges", response_model=List[NudgeResponse])
def get_nudges(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    one_day_ago = datetime.utcnow() - timedelta(days=1)

    conversations = (
        db.query(Conversation)
        .filter(
            (Conversation.initiator_id == current_user.id)
            | (Conversation.receiver_id == current_user.id)
        )
        .filter(Conversation.last_message_at >= one_day_ago)
        .all()
    )

    nudges = []
    for conv in conversations:
        other_user_id = (
            conv.receiver_id
            if conv.initiator_id == current_user.id
            else conv.initiator_id
        )
        other_user = db.query(User).filter(User.id == other_user_id).first()

        unread_count = (
            db.query(Message)
            .filter(
                Message.conversation_id == conv.id,
                Message.sender_id == other_user_id,
                Message.is_read == False,
            )
            .count()
        )

        if unread_count > 0 or (
            conv.last_message_at > one_day_ago
            and conv.last_message_at <= datetime.utcnow() - timedelta(hours=1)
        ):
            nudges.append(
                {
                    "conversation_id": conv.id,
                    "other_user_id": other_user_id,
                    "other_username": other_user.username if other_user else None,
                    "unread_count": unread_count,
                    "last_message_at": conv.last_message_at,
                }
            )

    return nudges


@router.get("/unread-count", response_model=dict)
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(
            (Conversation.initiator_id == current_user.id)
            | (Conversation.receiver_id == current_user.id)
        )
        .all()
    )

    total_unread = 0
    for conv in conversations:
        other_user_id = (
            conv.receiver_id
            if conv.initiator_id == current_user.id
            else conv.initiator_id
        )
        count = (
            db.query(Message)
            .filter(
                Message.conversation_id == conv.id,
                Message.sender_id == other_user_id,
                Message.is_read == False,
            )
            .count()
        )
        total_unread += count

    return {"unread_count": total_unread}
