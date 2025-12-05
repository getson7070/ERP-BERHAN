"""Create orders table to match erp.models.order.Order.

This migration creates the `orders` table with the columns expected by
`erp.models.order.Order` and the analytics dashboard:

- id
- organization_id  (FK → organizations.id)
- user_id          (FK → users.id, nullable)
- status
- currency
- total_amount
- placed_at / paid_at / shipped_at
- created_at / updated_at

It relies on `add_organizations_table` having already created the
`organizations` table and on the existing `users` table from the base schema.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_orders_table"
down_revision: Union[str, None] = "add_organizations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the orders table and its indexes."""
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        # Matches Order.organization_id: Mapped[int] = mapped_column(
        #     ForeignKey("organizations.id"), index=True, nullable=False
        # )
        sa.Column(
            "organization_id",
            sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Matches Order.user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="ETB",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        # TimestampMixin-style fields, consistent with other tables
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

    # Explicit indexes to match the analytics query patterns:
    # - filter by organization_id, status
    # - order/group by placed_at
    op.create_index(
        "ix_orders_organization_id",
        "orders",
        ["organization_id"],
    )
    op.create_index(
        "ix_orders_status",
        "orders",
        ["status"],
    )
    op.create_index(
        "ix_orders_placed_at",
        "orders",
        ["placed_at"],
    )


def downgrade() -> None:
    """Drop orders table and its indexes."""
    op.drop_index("ix_orders_placed_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_organization_id", table_name="orders")
    op.drop_table("orders")
