"""add retention columns"""

from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5g6"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "retain_until",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(NOW() + INTERVAL '7 years')"),
        ),
    )
    op.add_column(
        "audit_logs",
        sa.Column(
            "retain_until",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(NOW() + INTERVAL '10 years')"),
        ),
    )
    op.create_check_constraint(
        "users_retain_until_future", "users", "retain_until > NOW()"
    )
    op.create_check_constraint(
        "audit_logs_retain_after_create",
        "audit_logs",
        "retain_until >= created_at",
    )


def downgrade() -> None:
    op.drop_constraint("audit_logs_retain_after_create", "audit_logs")
    op.drop_constraint("users_retain_until_future", "users")
    op.drop_column("audit_logs", "retain_until")
    op.drop_column("users", "retain_until")
