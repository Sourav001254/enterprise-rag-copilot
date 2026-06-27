# alembic/versions/002_add_unique_constraint.py
"""add unique constraint to token_budgets

Revision ID: 002
Revises: 001
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_user_date', 'token_budgets', ['user_id', 'date'])

def downgrade() -> None:
    op.drop_constraint('uq_user_date', 'token_budgets', type_='unique')
