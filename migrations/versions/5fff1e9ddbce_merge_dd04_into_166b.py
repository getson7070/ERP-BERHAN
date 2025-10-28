"""merge dd04 into 166b

Revision ID: 5fff1e9ddbce
Revises: 166b3447697c, dd04f2776869
Create Date: 2025-10-28 15:49:05.631072
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5fff1e9ddbce'
down_revision = ('166b3447697c', 'dd04f2776869')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
