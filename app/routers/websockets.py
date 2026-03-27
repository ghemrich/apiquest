"""WebSocket endpoints — real-time leaderboard and notification channels."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.kafka.websocket_manager import leaderboard_manager, notification_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/leaderboard")
async def ws_leaderboard(websocket: WebSocket):
    """Subscribe to real-time leaderboard updates.

    Broadcasts global rank changes whenever a challenge is solved.
    No authentication required for the leaderboard feed.
    """
    await leaderboard_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; client can send ping text
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        leaderboard_manager.disconnect(websocket)


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    """Subscribe to personal notifications (badges, streaks, track completions).

    Client must send a JSON message with user_id after connecting:
      {"user_id": "<uuid>"}
    """
    await notification_manager.connect(websocket)
    try:
        # First message must identify the user
        init = await websocket.receive_json()
        user_id = init.get("user_id")
        if user_id:
            websocket.state.user_id = str(user_id)
            await websocket.send_json({"type": "connected", "user_id": str(user_id)})
        else:
            await websocket.send_json({"type": "error", "detail": "user_id required"})
            await websocket.close()
            return

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
