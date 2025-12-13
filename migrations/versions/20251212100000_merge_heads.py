"""Merge head (kept for compatibility).

Revision ID: 20251212100000
Revises: 0001_add_users_uuid
Create Date: 2025-12-12
"""

from alembic import op


revision = "20251212100000"
down_revision = "0001_add_users_uuid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge placeholder (linear chain compatibility)
    pass


def downgrade() -> None:
    pass
