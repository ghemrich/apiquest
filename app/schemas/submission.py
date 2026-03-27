import uuid
from datetime import datetime

from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    method: str
    path: str
    headers: dict | None = None
    query_params: dict | None = None
    body: dict | list | None = None


class PartialMatch(BaseModel):
    method: bool
    path: bool
    headers: bool
    body: bool


class SubmissionResponse(BaseModel):
    is_correct: bool
    feedback: str
    partial_matches: PartialMatch | None = None
    points_earned: int | None = None
    first_attempt_bonus: bool | None = None
    total_points: int | None = None
    badges_earned: list[str] | None = None
    next_challenge: str | None = None
    hints_available: int | None = None
    hint_endpoint: str | None = None


class SubmissionHistory(BaseModel):
    id: uuid.UUID
    challenge_id: uuid.UUID
    is_correct: bool
    points_earned: int
    submitted_at: datetime

    model_config = {"from_attributes": True}
