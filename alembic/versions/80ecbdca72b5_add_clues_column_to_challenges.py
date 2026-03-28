"""add clues column to challenges

Revision ID: 80ecbdca72b5
Revises: 0d5e3c58be47
Create Date: 2026-03-28 22:33:37.871329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80ecbdca72b5'
down_revision: Union[str, None] = '0d5e3c58be47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('challenges', sa.Column('clues', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('challenges', 'clues')
