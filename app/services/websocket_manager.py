from typing import Dict, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_message(self, message: str, exclude_user: int = None):
        for user_id, connections in self.active_connections.items():
            if user_id == exclude_user:
                continue
            disconnected = set()
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)


manager = ConnectionManager()


def create_message_payload(event_type: str, data: dict) -> str:
    return json.dumps({"type": event_type, "data": data})
