"""Merge ce91d3657d20 and add_user_dashboards into a single head.

This migration is a NO-OP merge revision whose sole purpose is to
unify the Alembic graph so that `alembic upgrade head` has a single
terminal head and `init_db.py` can run without multiple-head errors.
"""

from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# ----------------------------------------------------------------------
# Alembic identifiers
# ----------------------------------------------------------------------

# NEW revision id for this merge node. It must be unique.
revision = "merge_ce91d3657d20_add_user_dashboards"
# IMPORTANT:
# These two must match the CURRENT heads in your tree.
# Based on the audit, they are:
#   - "ce91d3657d20"
#   - "add_user_dashboards"
down_revision = ("ce91d3657d20", "add_user_dashboards")

branch_labels = None
depends_on = None


def upgrade() -> None:
    """Schema upgrade.

    This is a pure graph merge – no schema changes are applied here.
    The two branches already contain their respective DDL changes.
    """
    # Intentionally empty.
    pass


def downgrade() -> None:
    """Schema downgrade.

    Downgrading past a merge node is generally not supported in a
    meaningful way; this is left as a no-op.
    """
    # Intentionally empty.
    pass
