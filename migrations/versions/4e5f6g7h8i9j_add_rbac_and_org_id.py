"""add rbac and org id columns

Revision ID: 4e5f6g7h8i9j
Revises: 3d4e5f6g7h8i
Create Date: 2024-06-08 00:00:00 UTC
"""
from alembic import op
import sqlalchemy as sa

revision = '4e5f6g7h8i9j'
down_revision = '3d4e5f6g7h8i'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
    )
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('org_id', sa.Integer, sa.ForeignKey('organizations.id')),
        sa.Column('name', sa.String(), nullable=False),
    )
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
    )
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id'), primary_key=True),
        sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id'), primary_key=True),
    )
    op.create_table(
        'role_assignments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id')),
        sa.Column('org_id', sa.Integer, sa.ForeignKey('organizations.id')),
    )
    for table in ('orders', 'tenders', 'inventory'):
        op.add_column(table, sa.Column('org_id', sa.Integer, sa.ForeignKey('organizations.id')))


def downgrade():
    for table in ('orders', 'tenders', 'inventory'):
        op.drop_column(table, 'org_id')
    op.drop_table('role_assignments')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('organizations')
