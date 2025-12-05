"""Stub parent for banking / treasury branch.

WHY THIS EXISTS
---------------
The Alembic graph contains a merge revision f7a87f922530 whose
down_revision tuple is:

    ("35aef64fca2d", "7f0b76d5d3f1", "d6c63256408b")

However, the revision ID `7f0b76d5d3f1` was missing, causing:

    KeyError: '7f0b76d5d3f1'

This stub defines that missing revision and anchors it after the
finance GL tables revision (8f5c2e7d9a4b). It performs no schema
changes itself; all real banking/treasury tables are created in
later revisions.
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401  (imported for consistency)
import sqlalchemy as sa  # noqa: F401


# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision: str = "7f0b76d5d3f1"
down_revision: Union[str, None] = "8f5c2e7d9a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op upgrade – this stub only exists to stabilise the graph."""
    # Intentionally empty.
    pass


def downgrade() -> None:
    """No-op downgrade – nothing to undo for this stub revision."""
    # Intentionally empty.
    pass
