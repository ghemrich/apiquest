"""Gamification service — badge checking, streak management, track completion."""

import uuid
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, Track
from app.models.gamification import Badge, UserBadge, UserTrackProgress
from app.models.submission import Submission
from app.models.user import User

# ---------- Streak management ----------

def update_streak(db: Session, user: User) -> None:
    """Update user streak based on last_active_date vs today."""
    today = date.today()
    if user.last_active_date == today:
        return  # already active today
    if user.last_active_date and (today - user.last_active_date).days == 1:
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.current_streak, user.longest_streak)
    user.last_active_date = today
    db.add(user)
    db.flush()


# ---------- Track progress ----------

def update_track_progress(
    db: Session,
    user_id: uuid.UUID,
    track_id: uuid.UUID,
    pending_challenge_id: uuid.UUID | None = None,
) -> UserTrackProgress:
    """Recount solved challenges for a user/track and mark completed if done.

    Pass *pending_challenge_id* when the current solve hasn't been persisted yet
    (i.e. called before create_submission).  Omit it for reconciliation runs.
    """
    progress = (
        db.query(UserTrackProgress)
        .filter(UserTrackProgress.user_id == user_id, UserTrackProgress.track_id == track_id)
        .first()
    )
    if not progress:
        progress = UserTrackProgress(user_id=user_id, track_id=track_id, challenges_completed=0)
        db.add(progress)
        db.flush()

    # Count actual distinct solved challenges (resilient to seed changes)
    solved_ids = set(
        row[0]
        for row in db.query(Submission.challenge_id)
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Challenge.track_id == track_id,
        )
        .distinct()
    )
    if pending_challenge_id is not None:
        solved_ids.add(pending_challenge_id)
    progress.challenges_completed = len(solved_ids)

    total_in_track = db.query(Challenge).filter(Challenge.track_id == track_id).count()
    if progress.challenges_completed >= total_in_track and not progress.completed_at:
        progress.completed_at = datetime.utcnow()

    db.flush()
    return progress


def is_track_completed(db: Session, user_id: uuid.UUID, track_id: uuid.UUID) -> bool:
    progress = (
        db.query(UserTrackProgress)
        .filter(UserTrackProgress.user_id == user_id, UserTrackProgress.track_id == track_id)
        .first()
    )
    return progress is not None and progress.completed_at is not None


# ---------- Badge evaluation ----------

def _has_badge(db: Session, user_id: uuid.UUID, badge_id: uuid.UUID) -> bool:
    return (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
        .first()
    ) is not None


def _award_badge(db: Session, user_id: uuid.UUID, badge_id: uuid.UUID) -> UserBadge:
    ub = UserBadge(user_id=user_id, badge_id=badge_id)
    db.add(ub)
    db.flush()
    return ub


def _count_solved(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .filter(Submission.user_id == user_id, Submission.is_correct == True)  # noqa: E712
        .scalar()
    ) or 0


def _count_solved_in_track(db: Session, user_id: uuid.UUID, track_title: str) -> int:
    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .join(Track, Challenge.track_id == Track.id)
        .filter(Submission.user_id == user_id, Submission.is_correct == True, Track.title == track_title)  # noqa: E712
        .scalar()
    ) or 0


def _count_first_attempt_solves(db: Session, user_id: uuid.UUID) -> int:
    """Count challenges where the user's first submission was correct."""
    # Subquery: first submission per challenge
    first_sub = (
        db.query(
            Submission.challenge_id,
            func.min(Submission.submitted_at).label("first_at"),
        )
        .filter(Submission.user_id == user_id)
        .group_by(Submission.challenge_id)
        .subquery()
    )
    return (
        db.query(func.count())
        .select_from(Submission)
        .join(first_sub, (Submission.challenge_id == first_sub.c.challenge_id) & (Submission.submitted_at == first_sub.c.first_at))
        .filter(Submission.user_id == user_id, Submission.is_correct == True)  # noqa: E712
        .scalar()
    ) or 0


def _count_completed_tracks(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(UserTrackProgress)
        .filter(UserTrackProgress.user_id == user_id, UserTrackProgress.completed_at.isnot(None))
        .count()
    )


def _count_solved_by_difficulty(db: Session, user_id: uuid.UUID, difficulty: str) -> int:
    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Challenge.difficulty == difficulty,
        )
        .scalar()
    ) or 0


def _total_challenges_by_difficulty(db: Session, difficulty: str) -> int:
    return db.query(Challenge).filter(Challenge.difficulty == difficulty).count()


def _count_speed_solves(db: Session, user_id: uuid.UUID) -> int:
    """Count challenges solved under the time limit."""
    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Challenge.time_limit_seconds.isnot(None),
            Submission.solve_duration_seconds.isnot(None),
            Submission.solve_duration_seconds <= Challenge.time_limit_seconds,
        )
        .scalar()
    ) or 0


def check_and_award_badges(db: Session, user_id: uuid.UUID) -> list[str]:
    """Evaluate all badge criteria for a user and award any newly earned badges.
    Returns list of newly earned badge names."""
    badges = db.query(Badge).all()
    if not badges:
        return []

    newly_earned: list[str] = []
    solved_count = _count_solved(db, user_id)

    for badge in badges:
        if _has_badge(db, user_id, badge.id):
            continue

        earned = False
        ct = badge.criteria_type

        if ct == "challenge_count":
            earned = solved_count >= badge.criteria_value
        elif ct == "track_complete":
            # criteria_value is unused; match by badge name → track title mapping
            track_map = {
                "REST Rookie": "REST Fundamentals",
                "Query Wizard": "Query Mastery",
                "Auth Master": "Auth & Security",
                "Data Explorer": "Data Relationships",
                "Bug Hunter": None,  # handled separately
                "Real-Time Pro": "Real-Time APIs",
                "System Architect": "System Design",
            }
            track_title = track_map.get(badge.name)
            if track_title:
                track = db.query(Track).filter(Track.title == track_title).first()
                if track:
                    earned = is_track_completed(db, user_id, track.id)
        elif ct == "challenge_count_in_track":
            # Bug Hunter: 5 Error Detective challenges
            count = _count_solved_in_track(db, user_id, "Error Detective")
            earned = count >= badge.criteria_value
        elif ct == "first_attempt_solves":
            earned = _count_first_attempt_solves(db, user_id) >= badge.criteria_value
        elif ct == "streak":
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                earned = user.current_streak >= badge.criteria_value
        elif ct == "all_tracks_complete":
            total_tracks = db.query(Track).count()
            earned = _count_completed_tracks(db, user_id) >= total_tracks and total_tracks > 0
        elif ct == "tier_complete":
            # Map badge name to difficulty tier
            tier_map = {
                "Beginner Graduate": "beginner",
                "Intermediate Graduate": "intermediate",
                "Advanced Graduate": "advanced",
            }
            difficulty = tier_map.get(badge.name)
            if difficulty:
                total = _total_challenges_by_difficulty(db, difficulty)
                solved = _count_solved_by_difficulty(db, user_id, difficulty)
                earned = solved >= total and total > 0
        elif ct == "all_challenges_complete":
            total = db.query(Challenge).count()
            earned = solved_count >= total and total > 0
        elif ct == "speed_solves":
            earned = _count_speed_solves(db, user_id) >= badge.criteria_value

        if earned:
            _award_badge(db, user_id, badge.id)
            newly_earned.append(badge.name)

    return newly_earned
