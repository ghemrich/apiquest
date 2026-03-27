"""WebSocket connection manager — manages active connections for real-time updates."""

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class _EventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class ConnectionManager:
    """Manages WebSocket connections for a specific channel."""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self._connections = [ws for ws in self._connections if ws is not websocket]

    async def broadcast(self, message: dict[str, Any]):
        """Send a message to all connected clients."""
        text = json.dumps(message, cls=_EventEncoder)
        stale: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)

    async def send_to_user(self, user_id: str, message: dict[str, Any]):
        """Send a message to connections tagged with a specific user_id."""
        text = json.dumps(message, cls=_EventEncoder)
        stale: list[WebSocket] = []
        for ws in self._connections:
            ws_user = getattr(ws.state, "user_id", None)
            if ws_user == user_id:
                try:
                    await ws.send_text(text)
                except Exception:
                    stale.append(ws)
        for ws in stale:
            self.disconnect(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Singleton managers for the two real-time channels
leaderboard_manager = ConnectionManager()
notification_manager = ConnectionManager()
