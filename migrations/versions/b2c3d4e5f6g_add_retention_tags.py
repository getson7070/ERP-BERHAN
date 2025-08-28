"""add retention tagging columns"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g_add_retention_tags"
down_revision = "a1b2c3d4e5f7_add_user_dashboards_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("delete_after", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("delete_after", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "anonymized", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
    )
    op.create_check_constraint(
        "audit_delete_after_check",
        "audit_logs",
        "delete_after IS NULL OR delete_after >= created_at",
    )
    op.create_check_constraint(
        "invoice_delete_after_check",
        "invoices",
        "delete_after IS NULL OR delete_after >= issued_at",
    )


def downgrade() -> None:
    op.drop_constraint("invoice_delete_after_check", "invoices", type_="check")
    op.drop_constraint("audit_delete_after_check", "audit_logs", type_="check")
    op.drop_column("users", "anonymized")
    op.drop_column("invoices", "delete_after")
    op.drop_column("audit_logs", "delete_after")
