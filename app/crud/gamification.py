import uuid

from sqlalchemy.orm import Session

from app.models.gamification import HintReveal


def count_hints_revealed(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    return (
        db.query(HintReveal)
        .filter(
            HintReveal.user_id == user_id,
            HintReveal.challenge_id == challenge_id,
        )
        .count()
    )


def get_max_hint_revealed(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    from sqlalchemy import func

    result = (
        db.query(func.max(HintReveal.hint_number))
        .filter(
            HintReveal.user_id == user_id,
            HintReveal.challenge_id == challenge_id,
        )
        .scalar()
    )
    return result or 0


def reveal_hint(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID, hint_number: int) -> HintReveal:
    existing = (
        db.query(HintReveal)
        .filter(
            HintReveal.user_id == user_id,
            HintReveal.challenge_id == challenge_id,
            HintReveal.hint_number == hint_number,
        )
        .first()
    )
    if existing:
        return existing

    hint_reveal = HintReveal(
        user_id=user_id,
        challenge_id=challenge_id,
        hint_number=hint_number,
    )
    db.add(hint_reveal)
    db.commit()
    db.refresh(hint_reveal)
    return hint_reveal
