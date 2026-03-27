"""User profile and stats endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.user import get_user_by_id, get_user_by_username
from app.dependencies import get_current_user, get_db
from app.models.challenge import Challenge, Track
from app.models.gamification import Badge, UserBadge, UserTrackProgress
from app.models.submission import Submission
from app.models.user import User
from app.schemas.gamification import BadgeResponse, TrackProgressResponse, UserStatsResponse
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ---------- Profile ----------


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    badge_names = (
        db.query(Badge.name)
        .join(UserBadge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.user_id == current_user.id)
        .all()
    )
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        total_points=current_user.total_points,
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        last_active_date=current_user.last_active_date,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        created_at=current_user.created_at,
        badges=[row[0] for row in badge_names],
    )


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile (username, avatar_url, bio)."""
    if data.username is not None and data.username != current_user.username:
        existing = get_user_by_username(db, data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        current_user.username = data.username

    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    if data.bio is not None:
        current_user.bio = data.bio

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    badge_names = (
        db.query(Badge.name)
        .join(UserBadge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.user_id == current_user.id)
        .all()
    )
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        total_points=current_user.total_points,
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        last_active_date=current_user.last_active_date,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        created_at=current_user.created_at,
        badges=[row[0] for row in badge_names],
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete the current user's account and all related data."""
    # Delete dependent data first (in order of foreign key dependencies)
    db.query(Submission).filter(Submission.user_id == current_user.id).delete()
    db.query(UserBadge).filter(UserBadge.user_id == current_user.id).delete()
    db.query(UserTrackProgress).filter(UserTrackProgress.user_id == current_user.id).delete()
    from app.models.gamification import HintReveal
    db.query(HintReveal).filter(HintReveal.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()


# ---------- Public profile ----------


class PublicUserResponse(UserResponse):
    """Public profile — excludes email."""
    email: str | None = None


@router.get("/{user_id}", response_model=PublicUserResponse)
def get_user_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get a user's public profile by ID."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return PublicUserResponse(
        id=user.id,
        username=user.username,
        total_points=user.total_points,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        last_active_date=user.last_active_date,
        avatar_url=user.avatar_url,
        bio=user.bio,
        created_at=user.created_at,
    )


# ---------- Stats ----------


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def get_user_stats(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get detailed statistics for a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    challenges_solved = (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .filter(Submission.user_id == user_id, Submission.is_correct == True)  # noqa: E712
        .scalar()
    ) or 0

    total_challenges = db.query(Challenge).count()

    badges_earned = db.query(UserBadge).filter(UserBadge.user_id == user_id).count()

    # Global rank: count users with more points + 1
    rank = (
        db.query(func.count(User.id))
        .filter(User.total_points > user.total_points)
        .scalar()
        or 0
    ) + 1

    # Average hints used per solved challenge
    avg_hints = (
        db.query(func.avg(Submission.hints_used))
        .filter(Submission.user_id == user_id, Submission.is_correct == True)  # noqa: E712
        .scalar()
    )

    # Average solve time (seconds) across correct submissions
    avg_solve = (
        db.query(func.avg(Submission.solve_duration_seconds))
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Submission.solve_duration_seconds.isnot(None),
        )
        .scalar()
    )

    # Tier progress — completion per difficulty level
    tier_parts: list[str] = []
    for diff in ("beginner", "intermediate", "advanced"):
        total_d = db.query(Challenge).filter(Challenge.difficulty == diff).count()
        if total_d == 0:
            continue
        solved_d = (
            db.query(func.count(func.distinct(Submission.challenge_id)))
            .join(Challenge, Submission.challenge_id == Challenge.id)
            .filter(
                Submission.user_id == user_id,
                Submission.is_correct == True,  # noqa: E712
                Challenge.difficulty == diff,
            )
            .scalar()
        ) or 0
        pct = round(solved_d / total_d * 100)
        tier_parts.append(f"{diff.capitalize()} {pct}%")
    tier_progress_str = " | ".join(tier_parts) if tier_parts else None

    completion_pct = (challenges_solved / total_challenges * 100) if total_challenges > 0 else 0.0

    return UserStatsResponse(
        total_points=user.total_points,
        global_rank=rank,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        challenges_solved=challenges_solved,
        badges_earned=badges_earned,
        completion_percentage=round(completion_pct, 1),
        average_hints_used=round(float(avg_hints), 2) if avg_hints is not None else None,
        average_solve_time=round(float(avg_solve), 2) if avg_solve is not None else None,
        tier_progress=tier_progress_str,
    )


# ---------- Badges ----------


@router.get("/{user_id}/badges", response_model=list[BadgeResponse])
def get_user_badges(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get all badges earned by a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = (
        db.query(Badge, UserBadge.earned_at)
        .join(UserBadge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at)
        .all()
    )

    return [
        BadgeResponse(
            id=badge.id,
            name=badge.name,
            description=badge.description,
            icon_url=badge.icon_url,
            earned_at=earned_at,
        )
        for badge, earned_at in rows
    ]


# ---------- Track Progress ----------


@router.get("/{user_id}/progress", response_model=list[TrackProgressResponse])
def get_user_progress(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get track-by-track progress for a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tracks = db.query(Track).order_by(Track.order_index).all()
    result = []

    for track in tracks:
        total = db.query(Challenge).filter(Challenge.track_id == track.id).count()
        progress = (
            db.query(UserTrackProgress)
            .filter(UserTrackProgress.user_id == user_id, UserTrackProgress.track_id == track.id)
            .first()
        )
        completed = progress.challenges_completed if progress else 0
        pct = (completed / total * 100) if total > 0 else 0.0

        result.append(TrackProgressResponse(
            track_id=track.id,
            track_title=track.title,
            challenges_completed=completed,
            total_challenges=total,
            completion_percentage=round(pct, 1),
            started_at=progress.started_at if progress else None,
            completed_at=progress.completed_at if progress else None,
        ))

    return result
