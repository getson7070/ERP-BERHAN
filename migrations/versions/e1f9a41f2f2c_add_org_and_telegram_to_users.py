"""Add org + telegram chat linkage to users for bot scoping

Revision ID: e1f9a41f2f2c
Revises: 7d2f3c4b5a6d, c8b3f8c4b8d1
Create Date: 2025-11-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1f9a41f2f2c'
down_revision = ('7d2f3c4b5a6d', 'c8b3f8c4b8d1')
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('org_id', sa.Integer(), nullable=False, server_default='1'),
    )
    op.add_column('users', sa.Column('telegram_chat_id', sa.String(length=128), nullable=True))
    op.create_foreign_key('fk_users_org', 'users', 'organizations', ['org_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_users_org_chat', 'users', ['org_id', 'telegram_chat_id'])
    op.create_index('ix_users_org_id', 'users', ['org_id'])
    op.create_index('ix_users_telegram_chat_id', 'users', ['telegram_chat_id'])

    # Drop the server default to avoid future silent defaults once backfilled
    op.alter_column('users', 'org_id', server_default=None)


def downgrade():
    op.drop_index('ix_users_telegram_chat_id', table_name='users')
    op.drop_index('ix_users_org_id', table_name='users')
    op.drop_constraint('uq_users_org_chat', 'users', type_='unique')
    op.drop_constraint('fk_users_org', 'users', type_='foreignkey')
    op.drop_column('users', 'telegram_chat_id')
    op.drop_column('users', 'org_id')
