from alembic import op
import sqlalchemy as sa

# <=32 chars so it's safe even if alembic_version is varchar(32)
revision = "20251010_seed_test_users_dev"
# Point to a real, existing merge head in this repo
down_revision = "cf161230ed7f"
branch_labels = None
depends_on = None

def upgrade():
    # placeholder/no-op: keeps the chain consistent
    pass

def downgrade():
    pass
