"""Merge commission gating and procurement trade heads

Revision ID: 20251212100000
Revises: 1a2b3c4d5e6f, 20251211124000
Create Date: 2025-12-12 10:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "20251212100000"
down_revision = ("1a2b3c4d5e6f", "20251211124000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge migration to unify multiple heads
    op.get_bind()


def downgrade() -> None:
    # Downgrade splits heads; no actions required.
    op.get_bind()
