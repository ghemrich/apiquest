"""add solve_duration_seconds to submissions

Revision ID: a1b2c3d4e5f6
Revises: 94e71ab7cb37
Create Date: 2026-03-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '94e71ab7cb37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('submissions', sa.Column('solve_duration_seconds', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('submissions', 'solve_duration_seconds')
