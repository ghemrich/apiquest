import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.challenge import get_challenge_by_id
from app.crud.gamification import count_hints_revealed, reveal_hint, get_max_hint_revealed
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.challenge import ChallengeResponse, HintResponse

router = APIRouter(prefix="/api/v1/challenges", tags=["Challenges"])

HINT_COSTS = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}


@router.get("/{challenge_id}", response_model=ChallengeResponse)
def get_challenge(
    challenge_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    hints_total = len(challenge.hints) if challenge.hints else 0
    hints_revealed = count_hints_revealed(db, current_user.id, challenge.id)

    # Parse clues from description — store them as first lines separated by newlines,
    # or use a convention. For now, description IS the clue text.
    clues = []
    if challenge.description:
        clues = [line.strip() for line in challenge.description.split("\n") if line.strip()]

    return ChallengeResponse(
        id=challenge.id,
        title=challenge.title,
        track=challenge.track.title,
        difficulty=challenge.difficulty.value,
        points_value=challenge.points_value,
        description=challenge.description,
        clues=clues,
        sandbox_base_url=challenge.sandbox_endpoint,
        hints_available=hints_total,
        hints_revealed=hints_revealed,
        submit_endpoint=f"POST /api/v1/challenges/{challenge.id}/submit",
        hint_endpoint=f"GET /api/v1/challenges/{challenge.id}/hints/{{n}}",
    )


@router.get("/{challenge_id}/hints/{hint_number}", response_model=HintResponse)
def get_hint(
    challenge_id: uuid.UUID,
    hint_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    hints = challenge.hints or []
    if hint_number < 1 or hint_number > len(hints):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hint number")

    # Must reveal hints in order
    max_revealed = get_max_hint_revealed(db, current_user.id, challenge.id)
    if hint_number > max_revealed + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You must reveal hint {max_revealed + 1} first",
        )

    reveal_hint(db, current_user.id, challenge.id, hint_number)

    cost = HINT_COSTS.get(hint_number, 25)
    hints_remaining = len(hints) - hint_number

    return HintResponse(
        hint_number=hint_number,
        hint=hints[hint_number - 1],
        point_cost=cost,
        hints_remaining=hints_remaining,
    )
