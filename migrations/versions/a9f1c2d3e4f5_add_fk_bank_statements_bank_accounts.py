"""add fk bank_statements.bank_account_id -> bank_accounts.id

Revision ID: a9f1c2d3e4f5
Revises: 9c2b4b3c6a5e
Create Date: 2025-11-22 15:00:00

This migration adds a foreign key from ``bank_statements.bank_account_id``
to ``bank_accounts.id``. It assumes that the banking integration tables
have already been created by revision ``9c2b4b3c6a5e``.
"""

from alembic import op
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "a9f1c2d3e4f5"
down_revision = "9c2b4b3c6a5e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "fk_bank_statements_bank_account_id_bank_accounts",
        "bank_statements",
        "bank_accounts",
        ["bank_account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_bank_statements_bank_account_id_bank_accounts",
        "bank_statements",
        type_="foreignkey",
    )
