from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # active_connections maps user_id (str) to a list of WebSocket objects
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # user_roles maps user_id (str) to their role (str)
        self.user_roles: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.user_roles[user_id] = role

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_roles:
                    del self.user_roles[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed, handled in disconnect
                    pass

    async def broadcast_to_role(self, role: str, message: dict):
        for user_id, user_role in self.user_roles.items():
            if user_role == role:
                await self.send_personal_message(message, user_id)

manager = ConnectionManager()
