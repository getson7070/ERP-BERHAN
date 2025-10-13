"""merge heads

Revision ID: d1b125e62d70
Revises: e75b638f0ca3
Create Date: 2025-10-02 14:21:17.315146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1b125e62d70'
down_revision = 'e75b638f0ca3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
