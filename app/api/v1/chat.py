from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import (
    User,
    Product,
    Conversation,
    Message,
    ProductStatus,
    NotificationType,
)
from app.schemas.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.websocket_manager import manager, create_message_payload
from app.api.v1.notifications import create_notification
from bleach import clean

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def sanitize_message_content(content: str) -> str:
    allowed_tags = ["b", "i", "u", "em", "strong"]
    return clean(content, tags=allowed_tags, strip=True)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product).filter(Product.id == conversation_data.product_id).first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot chat with yourself"
        )

    receiver = db.query(User).filter(User.id == conversation_data.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found"
        )

    existing = (
        db.query(Conversation)
        .filter(
            Conversation.product_id == conversation_data.product_id,
            Conversation.initiator_id == current_user.id,
            Conversation.receiver_id == conversation_data.receiver_id,
        )
        .first()
    )
    if existing:
        return existing

    conversation = Conversation(
        product_id=conversation_data.product_id,
        initiator_id=current_user.id,
        receiver_id=conversation_data.receiver_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations")
def list_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(
            (Conversation.initiator_id == current_user.id)
            | (Conversation.receiver_id == current_user.id)
        )
        .order_by(Conversation.last_message_at.desc())
        .all()
    )

    result = []
    for c in conversations:
        other_user = c.receiver if c.initiator_id == current_user.id else c.initiator
        product = c.product

        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == c.id)
            .order_by(Message.created_at.desc())
            .first()
        )

        unread_count = (
            db.query(Message)
            .filter(
                Message.conversation_id == c.id,
                Message.sender_id != current_user.id,
                Message.is_read == False,
            )
            .count()
        )

        result.append(
            {
                "id": c.id,
                "product_id": c.product_id,
                "initiator_id": c.initiator_id,
                "receiver_id": c.receiver_id,
                "last_message_at": c.last_message_at.isoformat(),
                "created_at": c.created_at.isoformat(),
                "product_title": product.title if product else None,
                "other_username": other_user.username,
                "other_profile_image": other_user.profile_image,
                "last_message": last_msg.content if last_msg else None,
                "unread": unread_count,
            }
        )

    return result


@router.get("/conversations/{conversation_id}")
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    if (
        conversation.initiator_id != current_user.id
        and conversation.receiver_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this conversation",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    result = [
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
    return result


@router.post(
    "/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == message_data.conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    if (
        conversation.initiator_id != current_user.id
        and conversation.receiver_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send message in this conversation",
        )

    message = Message(
        conversation_id=message_data.conversation_id,
        sender_id=current_user.id,
        content=sanitize_message_content(message_data.content),
    )

    conversation.last_message_at = datetime.utcnow()

    db.add(message)
    db.commit()
    db.refresh(message)

    recipient_id = (
        conversation.receiver_id
        if conversation.initiator_id == current_user.id
        else conversation.initiator_id
    )

    payload = create_message_payload(
        "new_message",
        {
            "conversation_id": conversation.id,
            "sender_id": current_user.id,
            "content": message_data.content,
        },
    )
    asyncio.create_task(manager.send_personal_message(payload, recipient_id))

    create_notification(
        db=db,
        user_id=recipient_id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="New Message",
        message=f"You have a new message from {current_user.username or current_user.phone}",
        related_id=conversation.id,
    )
    db.commit()

    return message


@router.post(
    "/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT
)
def mark_conversation_read(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    if (
        conversation.initiator_id != current_user.id
        and conversation.receiver_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != current_user.id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return None
