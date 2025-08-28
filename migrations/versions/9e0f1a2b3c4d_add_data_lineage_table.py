"""add data lineage table

Revision ID: 9e0f1a2b3c4d
Revises: 8d9e0f1a2b3c
Create Date: 2025-08-28
"""
from alembic import op
import sqlalchemy as sa

revision = '9e0f1a2b3c4d'
down_revision = '8d9e0f1a2b3c'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'data_lineage',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('table_name', sa.String(length=128), nullable=False),
        sa.Column('column_name', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('data_lineage')
