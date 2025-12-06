"""Stub migration: add_crm_leads_table

This stub exists to satisfy the migration dependency chain:
    add_crm_leads_table -> add_maintenance_tickets_table (head)

The real CRM leads table is already handled elsewhere in the codebase,
or will be added in a future concrete migration. For now, this is a
no-op so that Alembic can build a consistent revision graph.
"""

from alembic import op
import sqlalchemy as sa  # noqa: F401  (kept for future edits)

# ----------------------------------------------------------------------
# Alembic revision identifiers
# ----------------------------------------------------------------------
revision = "add_crm_leads_table"
down_revision = None  # separate branch; safe as a no-op base revision
branch_labels = ("crm_leads_chain",)
depends_on = None


def upgrade():
    """No-op upgrade.

    Intentionally empty – this stub only exists so that Alembic can
    resolve the revision chain that references 'add_crm_leads_table'.
    """
    pass


def downgrade():
    """No-op downgrade.

    Since upgrade does nothing, downgrade also does nothing.
    """
    pass
