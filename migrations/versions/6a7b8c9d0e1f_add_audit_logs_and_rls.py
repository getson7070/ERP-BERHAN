"""add audit logs table and row level security

Revision ID: 6a7b8c9d0e1f
Revises: 5f6g7h8i9j0k
Create Date: 2024-06-09 00:00:00 UTC
"""
from alembic import op
import sqlalchemy as sa

revision = '6a7b8c9d0e1f'
down_revision = '5f6g7h8i9j0k'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('org_id', sa.Integer, sa.ForeignKey('organizations.id')),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    for table in ('orders', 'tenders', 'inventory', 'audit_logs'):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")
        op.execute(
            f"CREATE POLICY org_rls ON {table} USING (org_id = current_setting('my.org_id')::int) WITH CHECK (org_id = current_setting('my.org_id')::int)"
        )


def downgrade():
    for table in ('audit_logs', 'orders', 'tenders', 'inventory'):
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_table('audit_logs')
