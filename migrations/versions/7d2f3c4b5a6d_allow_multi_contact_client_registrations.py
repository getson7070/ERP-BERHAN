"""Allow multiple contacts per TIN with org/email scoping.

Revision ID: 7d2f3c4b5a6d
Revises: 629f2a3a2519
Create Date: 2025-02-17
"""

from alembic import op
from sqlalchemy import inspect

revision = "7d2f3c4b5a6d"
down_revision = "629f2a3a2519"
branch_labels = None
depends_on = None


def _drop_constraint_if_exists(inspector, table: str, name: str) -> None:
    if not inspector.has_table(table):
        return  # Table doesn't exist yet—skip safely
    constraints = inspector.get_unique_constraints(table)
    if any(c.get("name") == name for c in constraints):
        op.drop_constraint(name, table, type_="unique")


def _drop_index_if_exists(inspector, table: str, name: str) -> None:
    if not inspector.has_table(table):
        return  # Table doesn't exist yet—skip safely
    indexes = inspector.get_indexes(table)
    if any(ix.get("name") == name for ix in indexes):
        op.drop_index(name, table_name=table)


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    # Guard: Skip if table missing (created in later branch)
    if not inspector.has_table("client_registrations"):
        return

    _drop_constraint_if_exists(inspector, "client_registrations", "uq_client_registrations_org_tin")
    _drop_index_if_exists(inspector, "client_registrations", "ix_client_registrations_tin")
    _drop_index_if_exists(inspector, "client_registrations", "ix_client_registrations_email")
    op.create_index(
        "ix_client_registrations_email",
        "client_registrations",
        ["email"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_client_registrations_org_tin_email",
        "client_registrations",
        ["org_id", "tin", "email"],
    )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    # Guard: Skip if table missing
    if not inspector.has_table("client_registrations"):
        return

    _drop_constraint_if_exists(inspector, "client_registrations", "uq_client_registrations_org_tin_email")
    _drop_index_if_exists(inspector, "client_registrations", "ix_client_registrations_email")

    op.create_unique_constraint(
        "uq_client_registrations_org_tin",
        "client_registrations",
        ["org_id", "tin"],
    )