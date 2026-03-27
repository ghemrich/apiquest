import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Difficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    challenges: Mapped[list["Challenge"]] = relationship(back_populates="track", order_by="Challenge.order_index")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    points_value: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_method: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_path: Mapped[str] = mapped_column(String(500), nullable=False)
    expected_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_query_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hints: Mapped[list | None] = mapped_column(JSON, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sandbox_endpoint: Mapped[str] = mapped_column(String(500), nullable=False)

    track: Mapped["Track"] = relationship(back_populates="challenges")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="challenge")  # noqa: F821
