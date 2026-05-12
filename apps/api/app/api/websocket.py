from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging
from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")

            agents = detect_intent(message)
            results = await process_with_agents(message, agents)
            response = await synthesize_response(results, message)

            await manager.send_message(json.dumps({
                "type": "response",
                "agent": ", ".join(agents),
                "content": response
            }), user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")