"""auto-merge heads

Revision ID: f7a87f922530
Revises: 35aef64fca2d, 7f0b76d5d3f1, d6c63256408b
Create Date: 2025-12-01 19:14:05.335536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7a87f922530'
down_revision = ('35aef64fca2d', '7f0b76d5d3f1', 'd6c63256408b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
