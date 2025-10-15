"""Auto-merge heads (000c349c7249, 20241007_0001, 20250830_fix_rls_policies, 20250913_add_fk_indexes, 20251003_fix_kpi_sales_mv, 20251010_merge_heads_auto, 20251010_mfa_fields, 20251012_widen_ver, 20251014_cleanup_single_head, 20251014_merge_heads_for_77, 20251014_merge_heads_stable, 20251014_merge_to_single_head, 20251015_merge_heads_final, 4879f87e41ba, 5f2f3e2cb2c1, 8d0e1f2g3h4i, a0e29d7d0f58, ae590e676162, appr_rev_20251013_202016, d1b125e62d70, erp_backbone_20251013_0930, i1j2k3l4m5n)"""
from alembic import op
import sqlalchemy as sa
revision = "automerge_20251015164041"
down_revision = ('000c349c7249', '20241007_0001', '20250830_fix_rls_policies', '20250913_add_fk_indexes', '20251003_fix_kpi_sales_mv', '20251010_merge_heads_auto', '20251010_mfa_fields', '20251012_widen_ver', '20251014_cleanup_single_head', '20251014_merge_heads_for_77', '20251014_merge_heads_stable', '20251014_merge_to_single_head', '20251015_merge_heads_final', '4879f87e41ba', '5f2f3e2cb2c1', '8d0e1f2g3h4i', 'a0e29d7d0f58', 'ae590e676162', 'appr_rev_20251013_202016', 'd1b125e62d70', 'erp_backbone_20251013_0930', 'i1j2k3l4m5n')
branch_labels = None
depends_on = None
def upgrade(): pass
def downgrade(): pass