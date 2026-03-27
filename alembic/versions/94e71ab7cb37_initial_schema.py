"""initial schema

Revision ID: 94e71ab7cb37
Revises: 
Create Date: 2026-03-27 21:31:20.565635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94e71ab7cb37'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("total_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # --- tracks ---
    op.create_table(
        "tracks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Enum("beginner", "intermediate", "advanced", "expert", name="difficulty"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # --- challenges ---
    op.create_table(
        "challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("track_id", sa.Uuid(), sa.ForeignKey("tracks.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Enum("beginner", "intermediate", "advanced", "expert", name="difficulty", create_type=False), nullable=False),
        sa.Column("points_value", sa.Integer(), nullable=False),
        sa.Column("expected_method", sa.String(10), nullable=False),
        sa.Column("expected_path", sa.String(500), nullable=False),
        sa.Column("expected_headers", sa.JSON(), nullable=True),
        sa.Column("expected_query_params", sa.JSON(), nullable=True),
        sa.Column("expected_body", sa.JSON(), nullable=True),
        sa.Column("expected_response", sa.JSON(), nullable=True),
        sa.Column("hints", sa.JSON(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("time_limit_seconds", sa.Integer(), nullable=True),
        sa.Column("sandbox_endpoint", sa.String(500), nullable=False),
    )

    # --- badges ---
    op.create_table(
        "badges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("criteria_type", sa.String(50), nullable=False),
        sa.Column("criteria_value", sa.Integer(), nullable=False),
        sa.Column("icon_url", sa.String(500), nullable=True),
    )

    # --- submissions ---
    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("challenge_id", sa.Uuid(), sa.ForeignKey("challenges.id"), nullable=False),
        sa.Column("submitted_method", sa.String(10), nullable=False),
        sa.Column("submitted_path", sa.String(500), nullable=False),
        sa.Column("submitted_headers", sa.JSON(), nullable=True),
        sa.Column("submitted_query_params", sa.JSON(), nullable=True),
        sa.Column("submitted_body", sa.JSON(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("points_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("hints_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # --- user_badges ---
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("badge_id", sa.Uuid(), sa.ForeignKey("badges.id"), nullable=False),
        sa.Column("earned_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # --- user_track_progress ---
    op.create_table(
        "user_track_progress",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("track_id", sa.Uuid(), sa.ForeignKey("tracks.id"), nullable=False),
        sa.Column("challenges_completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # --- hint_reveals ---
    op.create_table(
        "hint_reveals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("challenge_id", sa.Uuid(), sa.ForeignKey("challenges.id"), nullable=False),
        sa.Column("hint_number", sa.Integer(), nullable=False),
        sa.Column("revealed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # --- indexes ---
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_index("ix_submissions_challenge_id", "submissions", ["challenge_id"])
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_track_progress_user_id", "user_track_progress", ["user_id"])
    op.create_index("ix_hint_reveals_user_challenge", "hint_reveals", ["user_id", "challenge_id"])


def downgrade() -> None:
    op.drop_index("ix_hint_reveals_user_challenge", table_name="hint_reveals")
    op.drop_index("ix_user_track_progress_user_id", table_name="user_track_progress")
    op.drop_index("ix_user_badges_user_id", table_name="user_badges")
    op.drop_index("ix_submissions_challenge_id", table_name="submissions")
    op.drop_index("ix_submissions_user_id", table_name="submissions")
    op.drop_table("hint_reveals")
    op.drop_table("user_track_progress")
    op.drop_table("user_badges")
    op.drop_table("submissions")
    op.drop_table("badges")
    op.drop_table("challenges")
    op.drop_table("tracks")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS difficulty")
