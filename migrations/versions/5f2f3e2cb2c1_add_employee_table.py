"""add employees table

Revision ID: 5f2f3e2cb2c1
Revises: 
Create Date: 2025-10-13 09:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5f2f3e2cb2c1"
down_revision = None  # or set to your latest revision id if you already have one
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hired_at", sa.Date(), nullable=True),
        sa.Column("terminated_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_employees_email_unique", "employees", ["email"], unique=True)
    op.create_check_constraint(
        "ck_employees_status",
        "employees",
        "status IN ('active','inactive','terminated','on_leave')",
    )


def downgrade():
    op.drop_constraint("ck_employees_status", "employees", type_="check")
    op.drop_index("ix_employees_email_unique", table_name="employees")
    op.drop_table("employees")
