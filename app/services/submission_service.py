"""Submission service — orchestrates submission validation and scoring."""

import uuid

from sqlalchemy.orm import Session

from app.crud.submission import count_total_attempts, create_submission, has_solved_challenge
from app.models.submission import Submission
from app.services.validation_engine import ValidationResult, validate_submission


def check_already_solved(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> bool:
    return has_solved_challenge(db, user_id, challenge_id)


def get_attempt_number(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    return count_total_attempts(db, user_id, challenge_id) + 1


def get_first_attempt(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> Submission | None:
    return (
        db.query(Submission)
        .filter(Submission.user_id == user_id, Submission.challenge_id == challenge_id)
        .order_by(Submission.submitted_at.asc())
        .first()
    )


def validate(
    submitted_method: str,
    submitted_path: str,
    submitted_headers: dict | None,
    submitted_query_params: dict | None,
    submitted_body: dict | list | None,
    expected_method: str,
    expected_path: str,
    expected_headers: dict | None,
    expected_query_params: dict | None,
    expected_body: dict | list | None,
) -> ValidationResult:
    return validate_submission(
        submitted_method=submitted_method,
        submitted_path=submitted_path,
        submitted_headers=submitted_headers,
        submitted_query_params=submitted_query_params,
        submitted_body=submitted_body,
        expected_method=expected_method,
        expected_path=expected_path,
        expected_headers=expected_headers,
        expected_query_params=expected_query_params,
        expected_body=expected_body,
    )


def save_submission(
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
    solve_duration_seconds: float | None = None,
) -> Submission:
    return create_submission(
        db=db,
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
        solve_duration_seconds=solve_duration_seconds,
    )
