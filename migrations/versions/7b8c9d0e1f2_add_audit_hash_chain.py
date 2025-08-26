"""add hash chain to audit logs"""

revision = '7b8c9d0e1f2'
down_revision = '6a7b8c9d0e1f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('audit_logs', sa.Column('prev_hash', sa.String(length=64)))
    op.add_column('audit_logs', sa.Column('hash', sa.String(length=64), nullable=False))


def downgrade():
    op.drop_column('audit_logs', 'hash')
    op.drop_column('audit_logs', 'prev_hash')
