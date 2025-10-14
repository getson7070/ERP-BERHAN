"""merge all remaining heads to a single head (cleanup)

Revision ID: 20251014_cleanup_single_head
Revises: d1b125e62d70, 20251014_merge_to_single_head, 20250830_fix_rls_policies
Create Date: 2025-10-14 09:20:45
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251014_cleanup_single_head"
down_revision = ("d1b125e62d70", "20251014_merge_to_single_head", "20250830_fix_rls_policies")
branch_labels = None
depends_on = None

def upgrade():
    # merge-only
    pass

def downgrade():
    # merge-only no-op
    pass
