from fastapi import APIRouter, Depends,WebSocket
from app.schemas.notifications_schema import NotificationSchema





router = APIRouter()


class ConnectionManager:

    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id, websocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id):
        self.active_connections.pop(user_id, None)

    async def send_notification(self, user_id, message:NotificationSchema):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)


manager = ConnectionManager()



@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):

    await manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(user_id)