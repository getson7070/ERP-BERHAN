"""Merge Alembic heads 0001_add_users_uuid and 739649794424.

This is a merge-only revision. It performs no schema changes.
It exists to unify divergent migration branches so the app can boot
with a single head.

Heads merged:
- 0001_add_users_uuid
- 739649794424
"""

from __future__ import annotations

from alembic import op  # noqa: F401

# Revision identifiers, used by Alembic.
revision = "20251212100000"
down_revision = ("0001_add_users_uuid", "739649794424")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge revision: no-op by design.
    return


def downgrade() -> None:
    # Downgrading a merge revision is also a no-op; Alembic will
    # naturally re-split the branches based on graph traversal.
    return
