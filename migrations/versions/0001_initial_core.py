"""initial core tables

Revision ID: 0001_initial_core
Revises: 
Create Date: 2025-10-15 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email', name='uq_customers_email')
    )

    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('qty_on_hand', sa.Integer(), server_default='0', nullable=False),
        sa.Column('uom', sa.String(length=16), server_default='EA', nullable=False),
        sa.Column('cost', sa.Numeric(12,2), server_default='0', nullable=False),
        sa.Column('price', sa.Numeric(12,2), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.UniqueConstraint('sku', name='uq_items_sku')
    )
    op.create_index('ix_items_sku', 'items', ['sku'])

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('orders')
    op.drop_index('ix_items_sku', table_name='items')
    op.drop_table('items')
    op.drop_table('customers')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
