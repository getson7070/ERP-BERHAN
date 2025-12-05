"""Stub migration for maintenance tickets chain.

This revision exists purely to stabilise the Alembic graph.

- It provides a concrete revision ID `add_maintenance_tickets_table`
  so any historical references remain valid.
- It performs no schema changes in upgrade() or downgrade().

All real maintenance-related tables are created in later migrations.
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401  # imported for consistency with other revisions
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "add_maintenance_tickets_table"
down_revision: Union[str, None] = "add_crm_leads_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op upgrade – this revision only exists to anchor the graph."""
    # Intentionally empty: all real work is done in later revisions.
    pass


def downgrade() -> None:
    """No-op downgrade – nothing to undo for this stub revision."""
    # Intentionally empty.
    pass
