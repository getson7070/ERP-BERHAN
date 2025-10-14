"""merge all heads to a single head

Revision ID: 20251014_merge_to_single_head
Revises: 20251010_merge_heads_auto, 20251010_mfa_fields, a1b2c3d4e5f7, ae590e676162, c3d4e5f6g7h, i1j2k3l4m5n
Create Date: 2025-10-13 21:44:35
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251014_merge_to_single_head"
down_revision = ("20251010_merge_heads_auto", "20251010_mfa_fields", "a1b2c3d4e5f7", "ae590e676162", "c3d4e5f6g7h", "i1j2k3l4m5n")
branch_labels = None
depends_on = None

def upgrade():
    # merge-only
    pass

def downgrade():
    # this merge is not easily reversible; leave as no-op
    pass
