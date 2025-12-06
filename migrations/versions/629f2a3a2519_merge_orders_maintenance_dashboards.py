"""merge_orders_maintenance_dashboards

Revision ID: 629f2a3a2519
Revises: merge_ce91d3657d20_add_user_dashboards, add_maintenance_tickets_table, add_orders_table
Create Date: 2025-12-06 06:51:04.113744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '629f2a3a2519'
down_revision = ('merge_ce91d3657d20_add_user_dashboards', 'add_maintenance_tickets_table', 'add_orders_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
