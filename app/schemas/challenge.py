import uuid

from pydantic import BaseModel


class TrackResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    difficulty: str
    challenge_count: int
    your_progress: str
    unlocked: bool
    unlock_requirement: str | None = None

    model_config = {"from_attributes": True}


class TracksListResponse(BaseModel):
    tracks: list[TrackResponse]


class ChallengeListItem(BaseModel):
    id: uuid.UUID
    title: str
    difficulty: str
    points_value: int
    solved: bool = False

    model_config = {"from_attributes": True}


class ChallengeResponse(BaseModel):
    id: uuid.UUID
    title: str
    track: str
    difficulty: str
    points_value: int
    description: str
    clues: list[str]
    sandbox_base_url: str
    hints_available: int
    hints_revealed: int
    submit_endpoint: str
    hint_endpoint: str

    model_config = {"from_attributes": True}


class HintResponse(BaseModel):
    hint_number: int
    hint: str
    point_cost: int
    hints_remaining: int
