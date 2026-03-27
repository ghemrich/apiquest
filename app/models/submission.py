import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    challenge_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    submitted_method: Mapped[str] = mapped_column(String(10), nullable=False)
    submitted_path: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_query_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="submissions")  # noqa: F821
    challenge: Mapped["Challenge"] = relationship(back_populates="submissions")  # noqa: F821
