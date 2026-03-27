"""Leaderboard router — global, weekly, per-track rankings."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.gamification import LeaderboardResponse
from app.services.leaderboard_service import (
    get_global_leaderboard,
    get_track_leaderboard,
    get_weekly_leaderboard,
)

router = APIRouter(prefix="/api/v1/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=LeaderboardResponse)
def global_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = get_global_leaderboard(db, limit=100)
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
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    entries = get_weekly_leaderboard(db, week_start=monday, limit=100)
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
    entries = get_track_leaderboard(db, track_id=track_id, limit=50)
    return LeaderboardResponse(
        entries=entries,
        period=f"track-{track_id}",
        total_players=len(entries),
    )
