"""Auto-merge November 2025 heads into a single lineage.

Why this exists
---------------
Runtime auto-repair was generating ad-hoc merge revisions inside
containers because four heads were present:
- 21d4e5f6a7b8 (incidents/reliability)
- 3d5e6f7a8b90 (RBAC phase 2)
- a9f1c2d3e4f5 (bank statements FK)
- d0b1b1c4f7a0 (inventory items)

Committing this merge revision restores a single authoritative head so
subsequent deployments do not emit new merge files on startup.

Schema impact: none; this is a pure merge.
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "d6c63256408b"
down_revision = ("21d4e5f6a7b8", "3d5e6f7a8b90", "a9f1c2d3e4f5", "d0b1b1c4f7a0")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge only; no-op.
    pass


def downgrade() -> None:
    # Merge only; no-op.
    pass
