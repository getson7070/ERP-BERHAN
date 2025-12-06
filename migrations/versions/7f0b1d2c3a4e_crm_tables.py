"""Create CRM account, pipeline, ticket, and portal link tables.

NOTE:
- `tickets.assigned_to_id` is kept as an INTEGER field but WITHOUT a
  database-level foreign key to `users.id` because, in the current
  revision graph, the `users` table is not guaranteed to exist yet
  when this migration runs.
- Application logic can still treat `assigned_to_id` as a user ID;
  we can add a proper FK in a later migration once the chain is stable.
"""

from alembic import op
import sqlalchemy as sa

revision = "7f0b1d2c3a4e"
down_revision = "6b4de6d7a0a1"  # procurement purchase order tables
branch_labels = None
depends_on = None  # no hard dependency on users


def upgrade() -> None:
    # Accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_accounts_type"),
        "accounts",
        ["type"],
        unique=False,
    )

    # Pipelines table
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Tickets table
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=True),
        sa.Column(
            "assigned_to_id",
            sa.Integer(),
            nullable=True,
            # LOGICALLY a user ID, but NO FK at DB level for now
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tickets_account_id",
        "tickets",
        ["account_id"],
        unique=False,
    )

    # Portal links table
    op.create_table(
        "portal_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )


def downgrade() -> None:
    op.drop_table("portal_links")
    op.drop_index("ix_tickets_account_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_table("pipelines")
    op.drop_index(op.f("ix_accounts_type"), table_name="accounts")
    op.drop_table("accounts")
