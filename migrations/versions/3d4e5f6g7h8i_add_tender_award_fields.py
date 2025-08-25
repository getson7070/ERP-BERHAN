"""add award tracking fields to tenders"""
from alembic import op
import sqlalchemy as sa

revision = '3d4e5f6g7h8i'
down_revision = '2b3c4d5e6f7a'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('tenders') as batch:
        batch.add_column(sa.Column('awarded_to', sa.String(), nullable=True))
        batch.add_column(sa.Column('award_date', sa.Date(), nullable=True))

def downgrade():
    with op.batch_alter_table('tenders') as batch:
        batch.drop_column('award_date')
        batch.drop_column('awarded_to')
