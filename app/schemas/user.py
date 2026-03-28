import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    message: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str | None = None
    total_points: int
    current_streak: int
    longest_streak: int
    last_active_date: date | None = None
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime
    badges: list[str] = []
    next_step: str | None = None

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    id: uuid.UUID
    username: str
    total_points: int
    current_streak: int
    access_token: str
    refresh_token: str
    message: str

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    avatar_url: str | None = Field(None, max_length=500)
    bio: str | None = Field(None, max_length=500)
