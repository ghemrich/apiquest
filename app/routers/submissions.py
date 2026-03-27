import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.challenge import get_challenge_by_id, get_next_challenge
from app.crud.gamification import count_hints_revealed
from app.crud.submission import (
    count_total_attempts,
    create_submission,
    has_solved_challenge,
)
from app.dependencies import get_current_user, get_db
from app.kafka.events import (
    badge_earned_event,
    challenge_solved_event,
    challenge_submitted_event,
    streak_updated_event,
    track_completed_event,
)
from app.kafka.producer import (
    TOPIC_BADGE_EARNED,
    TOPIC_CHALLENGE_SOLVED,
    TOPIC_CHALLENGE_SUBMITTED,
    TOPIC_STREAK_UPDATED,
    TOPIC_TRACK_COMPLETED,
    emit_event,
)
from app.models.submission import Submission
from app.models.user import User
from app.schemas.submission import PartialMatch, SubmissionCreate, SubmissionResponse
from app.services.gamification_service import (
    check_and_award_badges,
    update_streak,
    update_track_progress,
)
from app.services.validation_engine import validate_submission

router = APIRouter(prefix="/api/v1/challenges", tags=["Submissions"])

HINT_COSTS = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}


def _calculate_hint_penalty(hints_used: int) -> int:
    total = 0
    for i in range(1, hints_used + 1):
        total += HINT_COSTS.get(i, 25)
    return total


def _calculate_points(
    base_points: int,
    attempt_number: int,
    hints_used: int,
    current_streak: int = 0,
    time_limit_seconds: int | None = None,
    solve_duration_seconds: float | None = None,
) -> int:
    hint_penalty = _calculate_hint_penalty(hints_used)

    if attempt_number == 1:
        multiplier = 2.0
    elif attempt_number == 2:
        multiplier = 1.5
    else:
        multiplier = 1.0

    time_bonus = 0.0
    if time_limit_seconds and solve_duration_seconds is not None and solve_duration_seconds <= time_limit_seconds:
        time_bonus = base_points * 0.5

    streak_bonus = min(current_streak, 7) * 25

    final = (base_points - hint_penalty) * multiplier + time_bonus + streak_bonus
    minimum = base_points * 0.1
    return max(int(final), int(minimum))


def _fire_events(events: list[tuple[str, dict]]):
    """Run emit_event calls in an event loop (for use in BackgroundTasks)."""
    loop = asyncio.new_event_loop()
    try:
        for topic, event in events:
            loop.run_until_complete(emit_event(topic, event))
    finally:
        loop.close()


@router.post("/{challenge_id}/submit", response_model=SubmissionResponse)
def submit_solution(
    challenge_id: uuid.UUID,
    data: SubmissionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    # Check if already solved
    already_solved = has_solved_challenge(db, current_user.id, challenge.id)
    if already_solved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already solved this challenge",
        )

    # Run validation
    result = validate_submission(
        submitted_method=data.method,
        submitted_path=data.path,
        submitted_headers=data.headers,
        submitted_query_params=data.query_params,
        submitted_body=data.body,
        expected_method=challenge.expected_method,
        expected_path=challenge.expected_path,
        expected_headers=challenge.expected_headers,
        expected_query_params=challenge.expected_query_params,
        expected_body=challenge.expected_body,
    )

    hints_used = count_hints_revealed(db, current_user.id, challenge.id)
    attempt_number = count_total_attempts(db, current_user.id, challenge.id) + 1
    points_earned = 0

    # Calculate solve duration from first attempt on this challenge
    solve_duration: float | None = None
    first_attempt = (
        db.query(Submission)
        .filter(Submission.user_id == current_user.id, Submission.challenge_id == challenge.id)
        .order_by(Submission.submitted_at.asc())
        .first()
    )
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if first_attempt and first_attempt.submitted_at:
        first_at = first_attempt.submitted_at
        if first_at.tzinfo is None:
            from datetime import timezone as _tz
            first_at = first_at.replace(tzinfo=_tz.utc)
        solve_duration = (now - first_at).total_seconds()
    else:
        solve_duration = None  # first attempt — no prior timing data

    if result.is_correct:
        points_earned = _calculate_points(
            challenge.points_value,
            attempt_number,
            hints_used,
            current_streak=current_user.current_streak,
            time_limit_seconds=challenge.time_limit_seconds,
            solve_duration_seconds=solve_duration,
        )
        current_user.total_points += points_earned
        db.add(current_user)

        # Gamification: streak, track progress
        update_streak(db, current_user)
        track_progress = update_track_progress(db, current_user.id, challenge.track_id)

        # Track completion bonus: 500 × 1.5 = 750 bonus points
        if track_progress.completed_at is not None:
            track_bonus = int(500 * 1.5)
            points_earned += track_bonus
            current_user.total_points += track_bonus
            db.add(current_user)
    else:
        newly_earned = []

    # Save submission
    create_submission(
        db=db,
        user_id=current_user.id,
        challenge_id=challenge.id,
        submitted_method=data.method,
        submitted_path=data.path,
        submitted_headers=data.headers,
        submitted_query_params=data.query_params,
        submitted_body=data.body,
        is_correct=result.is_correct,
        points_earned=points_earned,
        hints_used=hints_used,
        feedback=result.feedback,
        solve_duration_seconds=solve_duration if result.is_correct else None,
    )

    # Badge check after submission is saved (so solved count is correct)
    if result.is_correct:
        newly_earned = check_and_award_badges(db, current_user.id)

        # Collect events to emit in background
        pending_events: list[tuple[str, dict]] = []

        # challenge.submitted
        pending_events.append((
            TOPIC_CHALLENGE_SUBMITTED,
            challenge_submitted_event(current_user.id, challenge.id, True),
        ))

        # challenge.solved
        pending_events.append((
            TOPIC_CHALLENGE_SOLVED,
            challenge_solved_event(
                user_id=current_user.id,
                username=current_user.username,
                challenge_id=challenge.id,
                points_earned=points_earned,
                total_points=current_user.total_points,
                badges_earned=newly_earned,
            ),
        ))

        # streak.updated
        pending_events.append((
            TOPIC_STREAK_UPDATED,
            streak_updated_event(
                user_id=current_user.id,
                current_streak=current_user.current_streak,
                longest_streak=current_user.longest_streak,
            ),
        ))

        # badge.earned (one event per badge)
        for badge_name in newly_earned:
            pending_events.append((
                TOPIC_BADGE_EARNED,
                badge_earned_event(user_id=current_user.id, badge_name=badge_name),
            ))

        # track.completed
        if track_progress.completed_at is not None:
            track = challenge.track
            pending_events.append((
                TOPIC_TRACK_COMPLETED,
                track_completed_event(
                    user_id=current_user.id,
                    track_id=challenge.track_id,
                    track_title=track.title if track else "Unknown",
                ),
            ))

        background_tasks.add_task(_fire_events, pending_events)
        next_ch = get_next_challenge(db, challenge)
        next_challenge_url = f"GET /api/v1/challenges/{next_ch.id}" if next_ch else None

        return SubmissionResponse(
            is_correct=True,
            feedback=result.feedback,
            points_earned=points_earned,
            first_attempt_bonus=attempt_number == 1,
            total_points=current_user.total_points,
            badges_earned=newly_earned,
            next_challenge=next_challenge_url,
        )

    # Incorrect
    background_tasks.add_task(
        _fire_events,
        [(TOPIC_CHALLENGE_SUBMITTED, challenge_submitted_event(current_user.id, challenge.id, False))],
    )
    hints_total = len(challenge.hints) if challenge.hints else 0
    return SubmissionResponse(
        is_correct=False,
        feedback=result.feedback,
        partial_matches=PartialMatch(
            method=result.method_match,
            path=result.path_match,
            headers=result.headers_match,
            body=result.body_match,
        ),
        hints_available=hints_total - hints_used,
        hint_endpoint=f"GET /api/v1/challenges/{challenge.id}/hints/{hints_used + 1}",
    )
