from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f38a77f2570a'
down_revision = '0001_initial_core'
branch_labels = None
depends_on = None

def upgrade():
    # No-op replacement migration (original script was broken/destructive).
    pass

def downgrade():
    # Irreversible stub.
    pass
