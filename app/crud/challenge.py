import uuid

from sqlalchemy.orm import Session

from app.models.challenge import Challenge, Track


def get_all_tracks(db: Session) -> list[Track]:
    return db.query(Track).order_by(Track.order_index).all()


def get_track_by_id(db: Session, track_id: uuid.UUID) -> Track | None:
    return db.query(Track).filter(Track.id == track_id).first()


def get_challenge_by_id(db: Session, challenge_id: uuid.UUID) -> Challenge | None:
    return db.query(Challenge).filter(Challenge.id == challenge_id).first()


def get_challenges_by_track(db: Session, track_id: uuid.UUID) -> list[Challenge]:
    return (
        db.query(Challenge)
        .filter(Challenge.track_id == track_id)
        .order_by(Challenge.order_index)
        .all()
    )


def get_next_challenge(db: Session, challenge: Challenge) -> Challenge | None:
    return (
        db.query(Challenge)
        .filter(
            Challenge.track_id == challenge.track_id,
            Challenge.order_index > challenge.order_index,
        )
        .order_by(Challenge.order_index)
        .first()
    )


def count_challenges_by_difficulty(db: Session, difficulty: str) -> int:
    return db.query(Challenge).filter(Challenge.difficulty == difficulty).count()
