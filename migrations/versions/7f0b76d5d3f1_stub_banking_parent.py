"""Stub migration to provide the missing parent for banking integration.

Revision ID: 7f0b76d5d3f1
Revises: 8f5c2e7d9a4b
Create Date: 2025-11-22 14:50:00

This migration intentionally does not perform any schema changes.

It exists solely to provide the missing parent for revision
``9c2b4b3c6a5e`` ("Add banking integration tables and extend bank_accounts")
so that Alembic can construct the revision map without a KeyError.
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "7f0b76d5d3f1"
down_revision = "8f5c2e7d9a4b"
branch_labels = None
depends_on = None


def upgrade():
    """No-op upgrade.

    This is a placeholder migration – it does not change the schema.
    """
    pass


def downgrade():
    """No-op downgrade.

    Since this migration does not change the schema, the downgrade
    is also a no-op.
    """
    pass
