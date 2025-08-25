"""add tender workflow columns"""
from alembic import op
import sqlalchemy as sa

revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('tenders') as batch:
        batch.add_column(sa.Column('workflow_state', sa.String(), nullable=False, server_default='advertised'))
        batch.add_column(sa.Column('result', sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table('tenders') as batch:
        batch.drop_column('result')
        batch.drop_column('workflow_state')
