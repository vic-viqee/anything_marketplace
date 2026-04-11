from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Conversation, Message
from app.services.websocket_manager import manager, create_message_payload

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    from app.services.auth_service import decode_token

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        await websocket.close(code=4001)
        return

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=4001)
            return
    finally:
        db.close()

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                event_type = payload.get("type")
                data = payload.get("data", {})

                if event_type == "ping":
                    await websocket.send_text(create_message_payload("pong", {}))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
