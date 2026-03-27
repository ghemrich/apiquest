"""Notification service — dispatches user notifications via WebSocket.

Wraps the WebSocket manager so consumers and other services don't depend
on the transport layer directly.
"""

import logging
from typing import Any

from app.kafka.websocket_manager import leaderboard_manager, notification_manager

logger = logging.getLogger(__name__)


async def notify_user(user_id: str, payload: dict[str, Any]) -> None:
    """Send a notification to a specific user's WebSocket channel."""
    await notification_manager.send_to_user(user_id, payload)


async def broadcast_leaderboard(payload: dict[str, Any]) -> None:
    """Broadcast a leaderboard update to all connected clients."""
    await leaderboard_manager.broadcast(payload)


async def notify_badge_earned(user_id: str, badge_name: str, earned_at: str | None = None) -> None:
    await notify_user(user_id, {
        "type": "badge",
        "badge_name": badge_name,
        "earned_at": earned_at,
    })


async def notify_streak_milestone(user_id: str, current_streak: int, longest_streak: int) -> None:
    await notify_user(user_id, {
        "type": "streak",
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "message": f"🔥 {current_streak}-day streak!",
    })


async def notify_track_completed(user_id: str, track_id: str, track_title: str) -> None:
    await notify_user(user_id, {
        "type": "track",
        "track_id": track_id,
        "track_title": track_title,
        "message": f"Track completed: {track_title}",
    })
