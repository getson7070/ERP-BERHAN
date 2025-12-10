"""Base empty revision for clean Alembic chain.

This migration does not change the schema. It only serves as the root
revision so that future migrations can build on a single, clean lineage.
"""

from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# Alembic revision identifiers
revision = "739649794424"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op upgrade for base revision."""
    # Intentionally empty – schema remains unchanged.
    pass


def downgrade() -> None:
    """No-op downgrade for base revision."""
    # Intentionally empty – schema remains unchanged.
    pass
