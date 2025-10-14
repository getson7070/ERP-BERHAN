
"""Merge multiple heads into a single linear head
Revision ID: 20251014_merge_heads_stable
Revises: 5f2f3e2cb2c1, erp_backbone_20251013_0930, appr_rev_20251013_202016, 20251014_cleanup_single_head, 20251012_widen_ver
Create Date: 2025-10-14 16:35:00
"""

# This is a merge-only revision. It does not change schema.
revision = "20251014_merge_heads_stable"
down_revision = ('5f2f3e2cb2c1', 'erp_backbone_20251013_0930', 'appr_rev_20251013_202016', '20251014_cleanup_single_head', '20251012_widen_ver')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
