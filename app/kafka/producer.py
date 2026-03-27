"""Kafka event producer — emits events to topics for async processing.

In production, uses aiokafka. In dev/test mode (or when Kafka is unavailable),
events are dispatched to in-process subscribers via the EventBus fallback.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------- Event Bus (in-process fallback for dev/test) ----------

class EventBus:
    """Simple in-process pub/sub for environments without Kafka."""

    def __init__(self):
        self._subscribers: dict[str, list] = defaultdict(list)

    def subscribe(self, topic: str, callback):
        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback):
        self._subscribers[topic] = [cb for cb in self._subscribers[topic] if cb is not callback]

    async def publish(self, topic: str, event: dict[str, Any]):
        for callback in self._subscribers[topic]:
            try:
                result = callback(topic, event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("EventBus subscriber error on topic %s", topic)

    def clear(self):
        self._subscribers.clear()


# Singleton event bus
event_bus = EventBus()


# ---------- JSON serializer ----------

class _EventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _serialize(event: dict) -> bytes:
    return json.dumps(event, cls=_EventEncoder).encode("utf-8")


# ---------- Kafka producer wrapper ----------

_producer = None
_use_kafka = False


async def start_kafka_producer(bootstrap_servers: str):
    """Start the aiokafka producer. Call during app startup."""
    global _producer, _use_kafka
    try:
        from aiokafka import AIOKafkaProducer
        _producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=_serialize,
        )
        await _producer.start()
        _use_kafka = True
        logger.info("Kafka producer started at %s", bootstrap_servers)
    except Exception:
        logger.warning("Kafka unavailable — using in-process EventBus fallback")
        _use_kafka = False


async def stop_kafka_producer():
    """Stop the Kafka producer. Call during app shutdown."""
    global _producer, _use_kafka
    if _producer:
        await _producer.stop()
        _producer = None
        _use_kafka = False
        logger.info("Kafka producer stopped")


async def emit_event(topic: str, event: dict[str, Any]):
    """Emit an event to a Kafka topic, or fall back to in-process EventBus."""
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    if _use_kafka and _producer:
        await _producer.send_and_wait(topic, event)
        logger.debug("Kafka event sent: %s", topic)
    else:
        await event_bus.publish(topic, event)
        logger.debug("EventBus event dispatched: %s", topic)


# ---------- Topic constants ----------

TOPIC_CHALLENGE_SUBMITTED = "challenge.submitted"
TOPIC_CHALLENGE_SOLVED = "challenge.solved"
TOPIC_BADGE_EARNED = "badge.earned"
TOPIC_STREAK_UPDATED = "streak.updated"
TOPIC_TRACK_COMPLETED = "track.completed"
TOPIC_LEADERBOARD_UPDATED = "leaderboard.updated"
