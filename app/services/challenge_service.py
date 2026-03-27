"""Challenge service — challenge retrieval and progression logic."""

import uuid

from sqlalchemy.orm import Session

from app.crud.challenge import (
    count_challenges_by_difficulty,
    get_all_tracks,
    get_challenge_by_id,
    get_challenges_by_track,
    get_next_challenge,
    get_track_by_id,
)
from app.models.challenge import Challenge, Track

UNLOCK_THRESHOLD = 0.70

UNLOCK_REQUIREMENTS: dict[str, tuple[str, str]] = {
    "intermediate": ("beginner", "Complete 70% of Beginner tier challenges"),
    "advanced": ("intermediate", "Complete 70% of Intermediate tier challenges"),
    "expert": ("advanced", "Complete 70% of Advanced tier challenges"),
}


def list_tracks(db: Session) -> list[Track]:
    return get_all_tracks(db)


def get_track(db: Session, track_id: uuid.UUID) -> Track | None:
    return get_track_by_id(db, track_id)


def get_challenge(db: Session, challenge_id: uuid.UUID) -> Challenge | None:
    return get_challenge_by_id(db, challenge_id)


def list_challenges_in_track(db: Session, track_id: uuid.UUID) -> list[Challenge]:
    return get_challenges_by_track(db, track_id)


def next_challenge(db: Session, challenge: Challenge) -> Challenge | None:
    return get_next_challenge(db, challenge)


def is_track_unlocked(
    db: Session,
    track_difficulty: str,
    solved_by_difficulty: dict[str, int],
) -> tuple[bool, str | None]:
    """Check if a track is unlocked based on prior tier completion.

    Returns (unlocked, requirement_message).
    """
    if track_difficulty == "beginner":
        return True, None

    req = UNLOCK_REQUIREMENTS.get(track_difficulty)
    if not req:
        return True, None

    prereq_difficulty, message = req
    total = count_challenges_by_difficulty(db, prereq_difficulty)
    if total == 0:
        return True, None
    solved = solved_by_difficulty.get(prereq_difficulty, 0)
    if solved / total >= UNLOCK_THRESHOLD:
        return True, None
    return False, message
