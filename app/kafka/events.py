"""Event helper — builds typed event dicts for Kafka/EventBus emission."""

import uuid
from datetime import datetime, timezone
from typing import Any


def challenge_submitted_event(
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    is_correct: bool,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "challenge_id": str(challenge_id),
        "is_correct": is_correct,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }


def challenge_solved_event(
    user_id: uuid.UUID,
    username: str,
    challenge_id: uuid.UUID,
    points_earned: int,
    total_points: int,
    badges_earned: list[str],
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "username": username,
        "challenge_id": str(challenge_id),
        "points_earned": points_earned,
        "total_points": total_points,
        "badges_earned": badges_earned,
    }


def badge_earned_event(
    user_id: uuid.UUID,
    badge_name: str,
    badge_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "badge_id": str(badge_id) if badge_id else None,
        "badge_name": badge_name,
        "earned_at": datetime.now(timezone.utc).isoformat(),
    }


def streak_updated_event(
    user_id: uuid.UUID,
    current_streak: int,
    longest_streak: int,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


def track_completed_event(
    user_id: uuid.UUID,
    track_id: uuid.UUID,
    track_title: str,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id),
        "track_id": str(track_id),
        "track_title": track_title,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
