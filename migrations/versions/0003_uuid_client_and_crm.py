"""Add UUID columns to client and CRM tables.

- client_accounts.uuid
- crm_accounts.uuid
- crm_contacts.uuid
- support_tickets.uuid
- client_portal_links.uuid
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa

# Adjust these to match your real revision chain
revision = "0003_uuid_client_and_crm"
down_revision = "0002_uuid_and_tin_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1) client_accounts.uuid
    op.add_column(
        "client_accounts",
        sa.Column("uuid", sa.String(length=36), nullable=True),
    )
    rows = bind.execute(
        sa.text("SELECT id FROM client_accounts WHERE uuid IS NULL")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE client_accounts SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )
    op.alter_column("client_accounts", "uuid", nullable=False)
    op.create_index(
        "ix_client_accounts_uuid",
        "client_accounts",
        ["uuid"],
        unique=True,
    )

    # 2) crm_accounts.uuid
    op.add_column(
        "crm_accounts",
        sa.Column("uuid", sa.String(length=36), nullable=True),
    )
    rows = bind.execute(
        sa.text("SELECT id FROM crm_accounts WHERE uuid IS NULL")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE crm_accounts SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )
    op.alter_column("crm_accounts", "uuid", nullable=False)
    op.create_index(
        "ix_crm_accounts_uuid",
        "crm_accounts",
        ["uuid"],
        unique=True,
    )

    # 3) crm_contacts.uuid
    op.add_column(
        "crm_contacts",
        sa.Column("uuid", sa.String(length=36), nullable=True),
    )
    rows = bind.execute(
        sa.text("SELECT id FROM crm_contacts WHERE uuid IS NULL")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE crm_contacts SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )
    op.alter_column("crm_contacts", "uuid", nullable=False)
    op.create_index(
        "ix_crm_contacts_uuid",
        "crm_contacts",
        ["uuid"],
        unique=True,
    )

    # 4) support_tickets.uuid
    op.add_column(
        "support_tickets",
        sa.Column("uuid", sa.String(length=36), nullable=True),
    )
    rows = bind.execute(
        sa.text("SELECT id FROM support_tickets WHERE uuid IS NULL")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE support_tickets SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )
    op.alter_column("support_tickets", "uuid", nullable=False)
    op.create_index(
        "ix_support_tickets_uuid",
        "support_tickets",
        ["uuid"],
        unique=True,
    )

    # 5) client_portal_links.uuid
    op.add_column(
        "client_portal_links",
        sa.Column("uuid", sa.String(length=36), nullable=True),
    )
    rows = bind.execute(
        sa.text("SELECT id FROM client_portal_links WHERE uuid IS NULL")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE client_portal_links SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )
    op.alter_column("client_portal_links", "uuid", nullable=False)
    op.create_index(
        "ix_client_portal_links_uuid",
        "client_portal_links",
        ["uuid"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_client_portal_links_uuid", table_name="client_portal_links")
    op.drop_column("client_portal_links", "uuid")

    op.drop_index("ix_support_tickets_uuid", table_name="support_tickets")
    op.drop_column("support_tickets", "uuid")

    op.drop_index("ix_crm_contacts_uuid", table_name="crm_contacts")
    op.drop_column("crm_contacts", "uuid")

    op.drop_index("ix_crm_accounts_uuid", table_name="crm_accounts")
    op.drop_column("crm_accounts", "uuid")

    op.drop_index("ix_client_accounts_uuid", table_name="client_accounts")
    op.drop_column("client_accounts", "uuid")
