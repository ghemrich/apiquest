"""Kafka consumers — listen to event topics and push to WebSocket channels.

In production, runs aiokafka consumers in background tasks.
In dev/test mode, registers EventBus subscribers for the same topics.
"""

import asyncio
import logging
from typing import Any

from app.kafka.producer import (
    TOPIC_BADGE_EARNED,
    TOPIC_CHALLENGE_SOLVED,
    TOPIC_LEADERBOARD_UPDATED,
    TOPIC_STREAK_UPDATED,
    TOPIC_TRACK_COMPLETED,
    event_bus,
)
from app.kafka.websocket_manager import leaderboard_manager, notification_manager

logger = logging.getLogger(__name__)

_consumer_tasks: list[asyncio.Task] = []


# ---------- Event handlers (shared by Kafka consumer and EventBus) ----------

async def _handle_challenge_solved(topic: str, event: dict[str, Any]):
    """When a challenge is solved, broadcast leaderboard update."""
    await leaderboard_manager.broadcast({
        "type": "rank_change",
        "user_id": event.get("user_id"),
        "username": event.get("username"),
        "points_earned": event.get("points_earned"),
        "total_points": event.get("total_points"),
    })


async def _handle_badge_earned(topic: str, event: dict[str, Any]):
    """Notify the specific user about their new badge."""
    user_id = event.get("user_id")
    if user_id:
        await notification_manager.send_to_user(str(user_id), {
            "type": "badge",
            "badge_name": event.get("badge_name"),
            "badge_id": event.get("badge_id"),
            "earned_at": event.get("timestamp"),
        })


async def _handle_streak_updated(topic: str, event: dict[str, Any]):
    """Notify the user about streak milestones."""
    user_id = event.get("user_id")
    streak = event.get("current_streak", 0)
    # Only notify on milestone streaks (3, 5, 7, 10, 14, 21, 30...)
    milestones = {3, 5, 7, 10, 14, 21, 30, 50, 100}
    if streak in milestones and user_id:
        await notification_manager.send_to_user(str(user_id), {
            "type": "streak",
            "current_streak": streak,
            "longest_streak": event.get("longest_streak"),
            "message": f"🔥 {streak}-day streak!",
        })


async def _handle_track_completed(topic: str, event: dict[str, Any]):
    """Notify the user about track completion."""
    user_id = event.get("user_id")
    if user_id:
        await notification_manager.send_to_user(str(user_id), {
            "type": "track",
            "track_id": event.get("track_id"),
            "track_title": event.get("track_title"),
            "message": f"Track completed: {event.get('track_title')}",
        })


async def _handle_leaderboard_updated(topic: str, event: dict[str, Any]):
    """Broadcast leaderboard refresh to all connected clients."""
    await leaderboard_manager.broadcast({
        "type": "leaderboard_refresh",
        "leaderboard_type": event.get("leaderboard_type"),
        "entries": event.get("entries", []),
    })


# ---------- EventBus registration (dev/test without Kafka) ----------

def register_eventbus_consumers():
    """Register in-process event handlers for dev/test environments."""
    event_bus.subscribe(TOPIC_CHALLENGE_SOLVED, _handle_challenge_solved)
    event_bus.subscribe(TOPIC_BADGE_EARNED, _handle_badge_earned)
    event_bus.subscribe(TOPIC_STREAK_UPDATED, _handle_streak_updated)
    event_bus.subscribe(TOPIC_TRACK_COMPLETED, _handle_track_completed)
    event_bus.subscribe(TOPIC_LEADERBOARD_UPDATED, _handle_leaderboard_updated)
    logger.info("EventBus consumers registered")


def unregister_eventbus_consumers():
    """Remove all EventBus subscribers."""
    event_bus.clear()
    logger.info("EventBus consumers unregistered")


# ---------- Kafka consumer workers (production) ----------

async def _run_kafka_consumer(topic: str, handler, group_id: str):
    """Run a Kafka consumer for a single topic in a loop."""
    try:
        import json

        from aiokafka import AIOKafkaConsumer

        from app.config import settings

        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        await consumer.start()
        logger.info("Kafka consumer started: topic=%s group=%s", topic, group_id)
        try:
            async for msg in consumer:
                await handler(topic, msg.value)
        finally:
            await consumer.stop()
    except Exception:
        logger.exception("Kafka consumer failed for topic %s", topic)


async def start_kafka_consumers():
    """Start Kafka consumer background tasks."""
    consumers = [
        (TOPIC_CHALLENGE_SOLVED, _handle_challenge_solved, "leaderboard-group"),
        (TOPIC_BADGE_EARNED, _handle_badge_earned, "notification-badge-group"),
        (TOPIC_STREAK_UPDATED, _handle_streak_updated, "notification-streak-group"),
        (TOPIC_TRACK_COMPLETED, _handle_track_completed, "notification-track-group"),
        (TOPIC_LEADERBOARD_UPDATED, _handle_leaderboard_updated, "ws-leaderboard-group"),
    ]
    for topic, handler, group in consumers:
        task = asyncio.create_task(_run_kafka_consumer(topic, handler, group))
        _consumer_tasks.append(task)
    logger.info("Started %d Kafka consumer tasks", len(_consumer_tasks))


async def stop_kafka_consumers():
    """Cancel all Kafka consumer background tasks."""
    for task in _consumer_tasks:
        task.cancel()
    _consumer_tasks.clear()
    logger.info("Kafka consumer tasks cancelled")
