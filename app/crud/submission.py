import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.submission import Submission


def create_submission(
    db: Session,
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    submitted_method: str,
    submitted_path: str,
    submitted_headers: dict | None,
    submitted_query_params: dict | None,
    submitted_body: dict | list | None,
    is_correct: bool,
    points_earned: int,
    hints_used: int,
    feedback: str,
) -> Submission:
    submission = Submission(
        user_id=user_id,
        challenge_id=challenge_id,
        submitted_method=submitted_method,
        submitted_path=submitted_path,
        submitted_headers=submitted_headers,
        submitted_query_params=submitted_query_params,
        submitted_body=submitted_body,
        is_correct=is_correct,
        points_earned=points_earned,
        hints_used=hints_used,
        feedback=feedback,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def count_correct_submissions(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    return (
        db.query(Submission)
        .filter(
            Submission.user_id == user_id,
            Submission.challenge_id == challenge_id,
            Submission.is_correct == True,  # noqa: E712
        )
        .count()
    )


def count_total_attempts(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    return (
        db.query(Submission)
        .filter(
            Submission.user_id == user_id,
            Submission.challenge_id == challenge_id,
        )
        .count()
    )


def has_solved_challenge(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> bool:
    return count_correct_submissions(db, user_id, challenge_id) > 0


def count_user_solved_challenges(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
        )
        .scalar()
        or 0
    )


def count_user_solved_in_track(db: Session, user_id: uuid.UUID, track_id: uuid.UUID) -> int:
    from app.models.challenge import Challenge

    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Challenge.track_id == track_id,
        )
        .scalar()
        or 0
    )


def count_user_solved_by_difficulty(db: Session, user_id: uuid.UUID, difficulty: str) -> int:
    from app.models.challenge import Challenge

    return (
        db.query(func.count(func.distinct(Submission.challenge_id)))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == user_id,
            Submission.is_correct == True,  # noqa: E712
            Challenge.difficulty == difficulty,
        )
        .scalar()
        or 0
    )
