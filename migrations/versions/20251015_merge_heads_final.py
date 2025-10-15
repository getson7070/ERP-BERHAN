from alembic import op
import sqlalchemy as sa

# Manual merge of Alembic heads to linearize tree.
revision = "20251015_merge_heads_final"
down_revision = ("20251014_merge_heads_for_77", "20251014_merge_heads_stable")
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
