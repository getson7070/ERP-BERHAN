"""your message

Revision ID: bba086713f12
Revises: d1b125e62d70
Create Date: 2025-10-02 16:37:32.264949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bba086713f12'
down_revision: Union[str, Sequence[str], None] = 'd1b125e62d70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
