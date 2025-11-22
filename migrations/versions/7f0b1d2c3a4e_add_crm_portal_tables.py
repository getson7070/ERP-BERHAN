"""Create CRM account, pipeline, ticket, and portal link tables."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7f0b1d2c3a4e"
down_revision: Union[str, None] = "6b4de6d7a0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "crm_accounts" not in inspector.get_table_names():
        op.create_table(
            "crm_accounts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("account_type", sa.String(length=32), nullable=False, server_default="customer"),
            sa.Column("pipeline_stage", sa.String(length=32), nullable=False, server_default="lead"),
            sa.Column("segment", sa.String(length=32), nullable=True),
            sa.Column("industry", sa.String(length=128), nullable=True),
            sa.Column("country", sa.String(length=64), nullable=True),
            sa.Column("city", sa.String(length=64), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("credit_limit", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
            sa.Column("payment_terms_days", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_crm_accounts_org_id", "crm_accounts", ["organization_id"], unique=False)
        op.create_index("ix_crm_accounts_code", "crm_accounts", ["code"], unique=False)
        op.create_index("ix_crm_accounts_pipeline", "crm_accounts", ["pipeline_stage"], unique=False)
        op.create_index("ix_crm_accounts_segment", "crm_accounts", ["segment"], unique=False)

    if "crm_contacts" not in inspector.get_table_names():
        op.create_table(
            "crm_contacts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=128), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_crm_contacts_org_id", "crm_contacts", ["organization_id"], unique=False)
        op.create_index("ix_crm_contacts_account_id", "crm_contacts", ["account_id"], unique=False)

    if "crm_pipeline_events" not in inspector.get_table_names():
        op.create_table(
            "crm_pipeline_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("from_stage", sa.String(length=32), nullable=False),
            sa.Column("to_stage", sa.String(length=32), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_crm_pipeline_events_org_id", "crm_pipeline_events", ["organization_id"], unique=False)
        op.create_index("ix_crm_pipeline_events_account_id", "crm_pipeline_events", ["account_id"], unique=False)

    if "support_tickets" not in inspector.get_table_names():
        op.create_table(
            "support_tickets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("subject", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_support_tickets_org_id", "support_tickets", ["organization_id"], unique=False)
        op.create_index("ix_support_tickets_account_id", "support_tickets", ["account_id"], unique=False)
        op.create_index("ix_support_tickets_status", "support_tickets", ["status"], unique=False)

    if "client_portal_links" not in inspector.get_table_names():
        op.create_table(
            "client_portal_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_client_portal_links_org_id", "client_portal_links", ["organization_id"], unique=False)
        op.create_index("ix_client_portal_links_user_id", "client_portal_links", ["user_id"], unique=True)
        op.create_index("ix_client_portal_links_account_id", "client_portal_links", ["account_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "client_portal_links" in inspector.get_table_names():
        op.drop_index("ix_client_portal_links_account_id", table_name="client_portal_links")
        op.drop_index("ix_client_portal_links_user_id", table_name="client_portal_links")
        op.drop_index("ix_client_portal_links_org_id", table_name="client_portal_links")
        op.drop_table("client_portal_links")

    if "support_tickets" in inspector.get_table_names():
        op.drop_index("ix_support_tickets_status", table_name="support_tickets")
        op.drop_index("ix_support_tickets_account_id", table_name="support_tickets")
        op.drop_index("ix_support_tickets_org_id", table_name="support_tickets")
        op.drop_table("support_tickets")

    if "crm_pipeline_events" in inspector.get_table_names():
        op.drop_index("ix_crm_pipeline_events_account_id", table_name="crm_pipeline_events")
        op.drop_index("ix_crm_pipeline_events_org_id", table_name="crm_pipeline_events")
        op.drop_table("crm_pipeline_events")

    if "crm_contacts" in inspector.get_table_names():
        op.drop_index("ix_crm_contacts_account_id", table_name="crm_contacts")
        op.drop_index("ix_crm_contacts_org_id", table_name="crm_contacts")
        op.drop_table("crm_contacts")

    if "crm_accounts" in inspector.get_table_names():
        op.drop_index("ix_crm_accounts_segment", table_name="crm_accounts")
        op.drop_index("ix_crm_accounts_pipeline", table_name="crm_accounts")
        op.drop_index("ix_crm_accounts_code", table_name="crm_accounts")
        op.drop_index("ix_crm_accounts_org_id", table_name="crm_accounts")
        op.drop_table("crm_accounts")
