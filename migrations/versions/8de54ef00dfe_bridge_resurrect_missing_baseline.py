"""bridge: resurrect missing baseline

Revision ID: 8de54ef00dfe
Revises: None
Create Date: 2025-10-16 18:03:36.821684
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8de54ef00dfe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass


