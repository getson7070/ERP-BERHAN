"""Create crm_leads table to match CrmLead model and analytics KPIs.

Revision ID: add_crm_leads_table
Revises: ce91d3657d20
Create Date: 2025-12-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_crm_leads_table"
down_revision: Union[str, None] = "ce91d3657d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create crm_leads table used by CrmLead model and analytics dashboard."""

    op.create_table(
        "crm_leads",
        sa.Column("id", sa.Integer, primary_key=True),
        # OrgScopedMixin → FK to organizations.id
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "potential_value",
            sa.Numeric(precision=18, scale=2),
            nullable=True,
        ),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_to_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Helpful indexes for analytics queries
    op.create_index(
        "ix_crm_leads_org_id",
        "crm_leads",
        ["org_id"],
    )
    op.create_index(
        "ix_crm_leads_status",
        "crm_leads",
        ["status"],
    )
    op.create_index(
        "ix_crm_leads_created_at",
        "crm_leads",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop crm_leads table and associated indexes."""

    op.drop_index("ix_crm_leads_created_at", table_name="crm_leads")
    op.drop_index("ix_crm_leads_status", table_name="crm_leads")
    op.drop_index("ix_crm_leads_org_id", table_name="crm_leads")
    op.drop_table("crm_leads")
