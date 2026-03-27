import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.challenge import get_all_tracks, get_track_by_id, get_challenges_by_track
from app.crud.submission import count_user_solved_in_track, has_solved_challenge, count_user_solved_by_difficulty
from app.crud.challenge import count_challenges_by_difficulty
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.challenge import TrackResponse, ChallengeListItem

router = APIRouter(prefix="/api/v1/tracks", tags=["Tracks"])

UNLOCK_THRESHOLD = 0.70  # 70% completion required

UNLOCK_REQUIREMENTS = {
    "intermediate": ("beginner", "Complete 70% of Beginner tier challenges"),
    "advanced": ("intermediate", "Complete 70% of Intermediate tier challenges"),
    "expert": ("advanced", "Complete 70% of Advanced tier challenges"),
}


def _is_track_unlocked(db: Session, user: User, difficulty: str) -> tuple[bool, str | None]:
    if difficulty == "beginner":
        return True, None

    req = UNLOCK_REQUIREMENTS.get(difficulty)
    if not req:
        return True, None

    prereq_difficulty, message = req
    total = count_challenges_by_difficulty(db, prereq_difficulty)
    if total == 0:
        return True, None

    solved = count_user_solved_by_difficulty(db, user.id, prereq_difficulty)
    if solved / total >= UNLOCK_THRESHOLD:
        return True, None

    return False, message


@router.get("", response_model=list[TrackResponse])
def list_tracks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tracks = get_all_tracks(db)
    result = []
    for track in tracks:
        total = len(track.challenges)
        solved = count_user_solved_in_track(db, current_user.id, track.id)
        unlocked, req = _is_track_unlocked(db, current_user, track.difficulty.value)
        result.append(
            TrackResponse(
                id=track.id,
                title=track.title,
                description=track.description,
                difficulty=track.difficulty.value,
                challenge_count=total,
                your_progress=f"{solved}/{total} completed",
                unlocked=unlocked,
                unlock_requirement=req,
            )
        )
    return result


@router.get("/{track_id}")
def get_track(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    track = get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    unlocked, req = _is_track_unlocked(db, current_user, track.difficulty.value)
    if not unlocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=req)

    challenges = get_challenges_by_track(db, track_id)
    challenge_list = []
    for c in challenges:
        solved = has_solved_challenge(db, current_user.id, c.id)
        challenge_list.append(
            ChallengeListItem(
                id=c.id,
                title=c.title,
                difficulty=c.difficulty.value,
                points_value=c.points_value,
                solved=solved,
            )
        )

    total = len(challenges)
    solved_count = count_user_solved_in_track(db, current_user.id, track_id)
    return {
        "id": track.id,
        "title": track.title,
        "description": track.description,
        "difficulty": track.difficulty.value,
        "challenge_count": total,
        "your_progress": f"{solved_count}/{total} completed",
        "challenges": challenge_list,
    }


@router.get("/{track_id}/challenges", response_model=list[ChallengeListItem])
def list_track_challenges(
    track_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    track = get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    unlocked, req = _is_track_unlocked(db, current_user, track.difficulty.value)
    if not unlocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=req)

    challenges = get_challenges_by_track(db, track_id)
    result = []
    for c in challenges:
        solved = has_solved_challenge(db, current_user.id, c.id)
        result.append(
            ChallengeListItem(
                id=c.id,
                title=c.title,
                difficulty=c.difficulty.value,
                points_value=c.points_value,
                solved=solved,
            )
        )
    return result
