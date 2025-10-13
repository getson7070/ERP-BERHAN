"""merge heads

Revision ID: e75b638f0ca3
Revises: 000c349c7249, a0e29d7d0f58
Create Date: 2025-10-02 10:29:05.432449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e75b638f0ca3"
down_revision = ("revL", "revM")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
