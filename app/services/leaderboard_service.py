"""Leaderboard service — caches leaderboard queries in Redis with 60s TTL."""

import json
import logging
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.gamification import UserBadge
from app.models.submission import Submission
from app.models.user import User
from app.schemas.gamification import LeaderboardEntry

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        from app.config import settings
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        logger.debug("Redis not available — leaderboard caching disabled")
        _redis_client = False  # mark as unavailable to avoid retry
        return None


def _get_cache(key: str) -> list[dict] | None:
    r = _get_redis()
    if not r:
        return None
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        logger.debug("Redis cache read failed for %s", key)
    return None


def _set_cache(key: str, value: list[dict], ttl: int = 60):
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        logger.debug("Redis cache write failed for %s", key)


def _entries_to_dicts(entries: list[LeaderboardEntry]) -> list[dict]:
    return [e.model_dump(mode="json") for e in entries]


def _dicts_to_entries(dicts: list[dict]) -> list[LeaderboardEntry]:
    return [LeaderboardEntry(**d) for d in dicts]


def get_global_leaderboard(db: Session, limit: int = 100) -> list[LeaderboardEntry]:
    cache_key = f"leaderboard:global:{limit}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return _dicts_to_entries(cached)

    badge_count_sub = (
        db.query(
            UserBadge.user_id,
            func.count(UserBadge.id).label("badge_count"),
        )
        .group_by(UserBadge.user_id)
        .subquery()
    )
    rows = (
        db.query(
            User.id,
            User.username,
            User.total_points,
            func.coalesce(badge_count_sub.c.badge_count, 0).label("badge_count"),
        )
        .outerjoin(badge_count_sub, User.id == badge_count_sub.c.user_id)
        .order_by(User.total_points.desc(), User.created_at.asc())
        .limit(limit)
        .all()
    )
    entries = [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=row.id,
            username=row.username,
            total_points=row.total_points,
            badges_count=row.badge_count,
        )
        for idx, row in enumerate(rows)
    ]
    _set_cache(cache_key, _entries_to_dicts(entries))
    return entries


def get_weekly_leaderboard(db: Session, week_start, limit: int = 100) -> list[LeaderboardEntry]:
    cache_key = f"leaderboard:weekly:{week_start.isoformat()}:{limit}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return _dicts_to_entries(cached)

    rows = (
        db.query(
            User.id,
            User.username,
            func.sum(Submission.points_earned).label("weekly_points"),
        )
        .join(Submission, Submission.user_id == User.id)
        .filter(Submission.is_correct == True, Submission.submitted_at >= week_start)  # noqa: E712
        .group_by(User.id, User.username)
        .order_by(func.sum(Submission.points_earned).desc(), User.created_at.asc())
        .limit(limit)
        .all()
    )
    entries = [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=row.id,
            username=row.username,
            total_points=int(row.weekly_points or 0),
            badges_count=0,
        )
        for idx, row in enumerate(rows)
    ]
    _set_cache(cache_key, _entries_to_dicts(entries))
    return entries


def get_track_leaderboard(db: Session, track_id: uuid.UUID, limit: int = 50) -> list[LeaderboardEntry]:
    cache_key = f"leaderboard:track:{track_id}:{limit}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return _dicts_to_entries(cached)

    rows = (
        db.query(
            User.id,
            User.username,
            func.sum(Submission.points_earned).label("track_points"),
        )
        .join(Submission, Submission.user_id == User.id)
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(Challenge.track_id == track_id, Submission.is_correct == True)  # noqa: E712
        .group_by(User.id, User.username)
        .order_by(func.sum(Submission.points_earned).desc(), User.created_at.asc())
        .limit(limit)
        .all()
    )
    entries = [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=row.id,
            username=row.username,
            total_points=int(row.track_points or 0),
            badges_count=0,
        )
        for idx, row in enumerate(rows)
    ]
    _set_cache(cache_key, _entries_to_dicts(entries))
    return entries
