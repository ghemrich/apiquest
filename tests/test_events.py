"""Tests for Kafka event bus, WebSocket manager, and WebSocket endpoints."""

import asyncio
import uuid

from fastapi.testclient import TestClient

from app.kafka.events import (
    badge_earned_event,
    challenge_solved_event,
    challenge_submitted_event,
    streak_updated_event,
    track_completed_event,
)
from app.kafka.producer import EventBus, emit_event, event_bus
from app.kafka.websocket_manager import ConnectionManager

# ---------- Event Bus tests ----------


class TestEventBus:
    def test_publish_subscribe(self):
        bus = EventBus()
        received = []

        async def handler(topic, event):
            received.append((topic, event))

        bus.subscribe("test.topic", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.publish("test.topic", {"data": "hello"})
        )
        assert len(received) == 1
        assert received[0][0] == "test.topic"
        assert received[0][1]["data"] == "hello"

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        async def handler(topic, event):
            received.append(event)

        bus.subscribe("test.topic", handler)
        bus.unsubscribe("test.topic", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.publish("test.topic", {"data": "hello"})
        )
        assert len(received) == 0

    def test_clear(self):
        bus = EventBus()
        received = []

        async def handler(topic, event):
            received.append(event)

        bus.subscribe("topic.a", handler)
        bus.subscribe("topic.b", handler)
        bus.clear()
        asyncio.get_event_loop().run_until_complete(bus.publish("topic.a", {}))
        asyncio.get_event_loop().run_until_complete(bus.publish("topic.b", {}))
        assert len(received) == 0

    def test_multiple_subscribers(self):
        bus = EventBus()
        results_a = []
        results_b = []

        async def handler_a(topic, event):
            results_a.append(event)

        async def handler_b(topic, event):
            results_b.append(event)

        bus.subscribe("test.topic", handler_a)
        bus.subscribe("test.topic", handler_b)
        asyncio.get_event_loop().run_until_complete(
            bus.publish("test.topic", {"value": 42})
        )
        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_subscriber_error_doesnt_break_others(self):
        bus = EventBus()
        received = []

        async def bad_handler(topic, event):
            raise ValueError("boom")

        async def good_handler(topic, event):
            received.append(event)

        bus.subscribe("test.topic", bad_handler)
        bus.subscribe("test.topic", good_handler)
        asyncio.get_event_loop().run_until_complete(
            bus.publish("test.topic", {"ok": True})
        )
        assert len(received) == 1

    def test_emit_event_uses_eventbus_fallback(self):
        received = []

        async def handler(topic, event):
            received.append((topic, event))

        event_bus.subscribe("challenge.submitted", handler)
        try:
            asyncio.get_event_loop().run_until_complete(
                emit_event("challenge.submitted", {"user_id": "abc"})
            )
            assert len(received) == 1
            assert received[0][1]["user_id"] == "abc"
            assert "timestamp" in received[0][1]
        finally:
            event_bus.unsubscribe("challenge.submitted", handler)


# ---------- Event builder tests ----------


class TestEventBuilders:
    def test_challenge_submitted_event(self):
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        event = challenge_submitted_event(uid, cid, True)
        assert event["user_id"] == str(uid)
        assert event["challenge_id"] == str(cid)
        assert event["is_correct"] is True
        assert "submitted_at" in event

    def test_challenge_solved_event(self):
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        event = challenge_solved_event(uid, "player1", cid, 100, 500, ["First Steps"])
        assert event["user_id"] == str(uid)
        assert event["username"] == "player1"
        assert event["points_earned"] == 100
        assert event["total_points"] == 500
        assert event["badges_earned"] == ["First Steps"]

    def test_badge_earned_event(self):
        uid = uuid.uuid4()
        bid = uuid.uuid4()
        event = badge_earned_event(uid, "REST Rookie", bid)
        assert event["badge_name"] == "REST Rookie"
        assert event["badge_id"] == str(bid)

    def test_streak_updated_event(self):
        uid = uuid.uuid4()
        event = streak_updated_event(uid, 5, 10)
        assert event["current_streak"] == 5
        assert event["longest_streak"] == 10

    def test_track_completed_event(self):
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        event = track_completed_event(uid, tid, "REST Fundamentals")
        assert event["track_title"] == "REST Fundamentals"
        assert "completed_at" in event


# ---------- Connection Manager tests ----------


class TestConnectionManager:
    def test_initial_state(self):
        mgr = ConnectionManager()
        assert mgr.active_count == 0


# ---------- WebSocket endpoint tests ----------


class TestWebSocketLeaderboard:
    def test_ws_leaderboard_connect_and_ping(self, client: TestClient):
        with client.websocket_connect("/ws/leaderboard") as ws:
            ws.send_text("ping")
            resp = ws.receive_text()
            assert resp == "pong"

    def test_ws_leaderboard_disconnect(self, client: TestClient):
        with client.websocket_connect("/ws/leaderboard") as ws:
            ws.send_text("ping")
            ws.receive_text()
        # Disconnected — no error


class TestWebSocketNotifications:
    def test_ws_notifications_connect_with_user_id(self, client: TestClient):
        uid = str(uuid.uuid4())
        with client.websocket_connect("/ws/notifications") as ws:
            ws.send_json({"user_id": uid})
            resp = ws.receive_json()
            assert resp["type"] == "connected"
            assert resp["user_id"] == uid

    def test_ws_notifications_missing_user_id(self, client: TestClient):
        with client.websocket_connect("/ws/notifications") as ws:
            ws.send_json({"not_user_id": "oops"})
            resp = ws.receive_json()
            assert resp["type"] == "error"

    def test_ws_notifications_ping_pong(self, client: TestClient):
        uid = str(uuid.uuid4())
        with client.websocket_connect("/ws/notifications") as ws:
            ws.send_json({"user_id": uid})
            ws.receive_json()  # connected msg
            ws.send_text("ping")
            resp = ws.receive_text()
            assert resp == "pong"


# ---------- Integration: events emitted on submission ----------


class TestSubmissionEvents:
    def test_correct_submission_emits_events(self, client, auth_header, sample_track, db):
        """Verify that solving a challenge fires EventBus events."""
        challenge = sample_track["challenge"]

        collected = []

        async def collector(topic, event):
            collected.append((topic, event))

        # Subscribe to all topics
        event_bus.subscribe("challenge.submitted", collector)
        event_bus.subscribe("challenge.solved", collector)
        event_bus.subscribe("streak.updated", collector)
        try:
            resp = client.post(
                f"/api/v1/challenges/{challenge.id}/submit",
                json={
                    "method": challenge.expected_method,
                    "path": challenge.expected_path,
                    "headers": challenge.expected_headers,
                    "query_params": challenge.expected_query_params,
                    "body": challenge.expected_body,
                },
                headers=auth_header,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_correct"] is True

            # Background tasks run synchronously in TestClient
            topics = [t for t, _ in collected]
            assert "challenge.submitted" in topics
            assert "challenge.solved" in topics
            assert "streak.updated" in topics
        finally:
            event_bus.unsubscribe("challenge.submitted", collector)
            event_bus.unsubscribe("challenge.solved", collector)
            event_bus.unsubscribe("streak.updated", collector)

    def test_incorrect_submission_emits_submitted_event(self, client, auth_header, sample_track, db):
        """Incorrect submissions should emit challenge.submitted only."""
        challenge = sample_track["challenge"]

        collected = []

        async def collector(topic, event):
            collected.append((topic, event))

        event_bus.subscribe("challenge.submitted", collector)
        event_bus.subscribe("challenge.solved", collector)
        try:
            resp = client.post(
                f"/api/v1/challenges/{challenge.id}/submit",
                json={
                    "method": "DELETE",
                    "path": "/wrong",
                },
                headers=auth_header,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_correct"] is False

            topics = [t for t, _ in collected]
            assert "challenge.submitted" in topics
            assert "challenge.solved" not in topics
        finally:
            event_bus.unsubscribe("challenge.submitted", collector)
            event_bus.unsubscribe("challenge.solved", collector)
