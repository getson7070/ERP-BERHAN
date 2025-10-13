"""auto-merge multiple alembic heads

Revision ID: 20251010_merge_heads_auto
Revises: ['20241007_0001', '20250913_add_fk_indexes', '20251003_fix_kpi_sales_mv',
          '20251010_mfa_fields', '4879f87e41ba', '8d0e1f2g3h4i', 'ae590e676162',
          'i1j2k3l4m5n']
Create Date: 2025-10-10 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251010_merge_heads_auto"
down_revision = ('20241007_0001', '20250913_add_fk_indexes', '20251003_fix_kpi_sales_mv',
                 '20251010_mfa_fields', '4879f87e41ba', '8d0e1f2g3h4i', 'ae590e676162',
                 'i1j2k3l4m5n')
branch_labels = None
depends_on = None

def upgrade():
    # Merge-only; no schema ops
    pass

def downgrade():
    # Merge-only; typically no-op
    pass
