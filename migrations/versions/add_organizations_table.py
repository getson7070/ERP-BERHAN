"""Create organizations table for multi-tenant isolation.

Revision ID: add_organizations_table
Revises: add_user_dashboards
Create Date: 2025-12-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_organizations_table"
down_revision: Union[str, None] = "add_user_dashboards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the organizations table.

    This matches erp.models.organization.Organization and gives a stable
    anchor for org_id / organization_id foreign keys.
    """
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    )


def downgrade() -> None:
    """Drop the organizations table."""
    op.drop_table("organizations")
