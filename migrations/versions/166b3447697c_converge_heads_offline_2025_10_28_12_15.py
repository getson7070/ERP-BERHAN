"""Converge heads (offline) 2025-10-28 12:15

Revision ID: 166b3447697c
Revises: 20251025_trusted_devices, 8de54ef00dfe, f38a77f2570a
Create Date: 2025-10-28 12:25:52.520736
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '166b3447697c'
down_revision = ('20251025_trusted_devices', '8de54ef00dfe', 'f38a77f2570a')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
