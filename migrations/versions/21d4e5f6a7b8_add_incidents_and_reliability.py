"""Add incidents table for reliability tracking."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "21d4e5f6a7b8"
down_revision = "0a1b2c3d4e7f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incidents",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("service", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("detail_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_incidents_org_id", "incidents", ["org_id"])
    op.create_index("ix_incidents_service", "incidents", ["service"])
    op.create_index("ix_incidents_status", "incidents", ["status"])


def downgrade():
    op.drop_table("incidents")
