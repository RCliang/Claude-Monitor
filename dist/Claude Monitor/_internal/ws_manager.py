"""WebSocket connection manager for real-time updates."""

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message_type: str, data: Any):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        payload = json.dumps({"type": message_type, "data": data})
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_to(self, websocket: WebSocket, message_type: str, data: Any):
        """Send a message to a specific client."""
        payload = json.dumps({"type": message_type, "data": data})
        try:
            await websocket.send_text(payload)
        except Exception:
            self.active_connections.remove(websocket)


# Global instance
manager = ConnectionManager()
