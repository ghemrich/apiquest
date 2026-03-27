"""Leaderboard router — global, weekly, per-track rankings."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.gamification import UserBadge
from app.models.user import User
from app.schemas.gamification import LeaderboardEntry, LeaderboardResponse

router = APIRouter(prefix="/api/v1/leaderboard", tags=["Leaderboard"])


def _build_leaderboard(db: Session, limit: int = 100) -> list[LeaderboardEntry]:
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
        .order_by(User.total_points.desc())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=row.id,
            username=row.username,
            total_points=row.total_points,
            badges_count=row.badge_count,
        )
        for idx, row in enumerate(rows)
    ]


@router.get("", response_model=LeaderboardResponse)
def global_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = _build_leaderboard(db, limit=100)
    return LeaderboardResponse(
        entries=entries,
        period="all-time",
        total_players=len(entries),
    )


@router.get("/weekly", response_model=LeaderboardResponse)
def weekly_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # For now, same as global — weekly filtering added when Kafka events land
    entries = _build_leaderboard(db, limit=100)
    return LeaderboardResponse(
        entries=entries,
        period="weekly",
        total_players=len(entries),
    )


@router.get("/track/{track_id}", response_model=LeaderboardResponse)
def track_leaderboard(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.challenge import Challenge
    from app.models.submission import Submission

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
        .order_by(func.sum(Submission.points_earned).desc())
        .limit(50)
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
    return LeaderboardResponse(
        entries=entries,
        period=f"track-{track_id}",
        total_players=len(entries),
    )
