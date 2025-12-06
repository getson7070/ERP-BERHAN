"""Auto-merge heads."""

from alembic import op
import sqlalchemy as sa

revision = 'f7a87f922530'
down_revision = ('35aef64fca2d', '7f0b76d5d3f1', 'd6c63256408b')  # FIXED: Proper merges
branch_labels = None
depends_on = None


def upgrade():
    # Merge—no changes
    pass


def downgrade():
    pass