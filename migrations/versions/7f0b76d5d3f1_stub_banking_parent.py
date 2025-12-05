"""Stub parent for finance GL tables.

WHY THIS EXISTS
---------------
Several later revisions (e.g. 8f5c2e7d9a4b_add_finance_gl_tables) reference
`7f0b1d2c3a4e` as their down_revision, but the actual revision file was
missing. That caused Alembic to raise `KeyError: '7f0b1d2c3a4e'` when
building the revision map.

This stub:

- Defines the missing revision ID `7f0b1d2c3a4e`.
- Anchors it after the user security spine (`a12b34c56d78`).
- Performs no schema changes itself.
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "7f0b1d2c3a4e"
down_revision: Union[str, None] = "a12b34c56d78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op upgrade for the finance stub parent."""
    pass


def downgrade() -> None:
    """No-op downgrade for the finance stub parent."""
    pass
