"""merge migration heads

Revision ID: a0e29d7d0f58
Revises: 20250913_add_fk_indexes, 8d0e1f2g3h4i, i1j2k3l4m5n
Create Date: 2025-09-26 16:47:24.494409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a0e29d7d0f58"
down_revision = ("20250913_add_fk_indexes", "8d0e1f2g3h4i", "i1j2k3l4m5n")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
