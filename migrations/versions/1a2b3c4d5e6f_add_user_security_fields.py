"""add security fields to users and password_resets table

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-09-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    cols = [row[1] for row in conn.execute(sa.text('PRAGMA table_info(users)'))]
    if 'failed_attempts' not in cols:
        op.add_column('users', sa.Column('failed_attempts', sa.Integer(), server_default='0'))
    if 'account_locked' not in cols:
        op.add_column('users', sa.Column('account_locked', sa.Boolean(), server_default='0'))
    if 'last_password_change' not in cols:
        op.add_column('users', sa.Column('last_password_change', sa.DateTime(), nullable=True))
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='password_resets'")).fetchone():
        op.create_table(
            'password_resets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
            sa.Column('token', sa.String(length=255), nullable=False, unique=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False)
        )


def downgrade():
    op.drop_table('password_resets')
    op.drop_column('users', 'last_password_change')
    op.drop_column('users', 'account_locked')
    op.drop_column('users', 'failed_attempts')
