"""Stub migration to provide the missing parent for banking integration."""

from alembic import op
import sqlalchemy as sa

revision = '7f0b76d5d3f1'
down_revision = '8f5c2e7d9a4b'  # From logs (finance GL)
branch_labels = None
depends_on = None


def upgrade():
    # Stub—no changes, just to link chain
    pass


def downgrade():
    pass