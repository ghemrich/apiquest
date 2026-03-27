import uuid
from datetime import datetime

from pydantic import BaseModel


class BadgeResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    icon_url: str | None = None
    earned_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserStatsResponse(BaseModel):
    total_points: int
    global_rank: int | None = None
    current_streak: int
    longest_streak: int
    challenges_solved: int
    badges_earned: int
    completion_percentage: float
    average_hints_used: float | None = None
    average_solve_time: float | None = None
    tier_progress: str | None = None

    model_config = {"from_attributes": True}


class TrackProgressResponse(BaseModel):
    track_id: uuid.UUID
    track_title: str
    challenges_completed: int
    total_challenges: int
    completion_percentage: float
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    total_points: int
    badges_count: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    period: str
    total_players: int
