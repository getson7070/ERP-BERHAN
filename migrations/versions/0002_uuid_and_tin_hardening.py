"""Add UUID identifiers and harden TIN rules for core entities.

- Adds uuid columns to users, employees, institutions, client_registrations
- Backfills uuid for existing rows
- Enforces Ethiopian TIN format: 10 digits, starting with 0
- Adds institution_type and registration-level institution_type
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# IMPORTANT: set these according to your current head revision
revision = "0002_uuid_and_tin_hardening"
down_revision = "0001_initial_core"
branch_labels = None
depends_on = None


def _uuid_type():
    """Cross-dialect UUID column type.

    - On Postgres, use native UUID type.
    - On SQLite and others, fall back to String(36).
    """
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # ------------------------------------------------------------------
    # 1) USERS: add uuid, backfill, enforce NOT NULL + unique
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column(
            "uuid",
            _uuid_type(),
            nullable=True,
        ),
    )

    # Backfill
    users = bind.execute(sa.text("SELECT id FROM users WHERE uuid IS NULL")).fetchall()
    for row in users:
        bind.execute(
            sa.text("UPDATE users SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )

    op.alter_column("users", "uuid", nullable=False)
    op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)

    # ------------------------------------------------------------------
    # 2) EMPLOYEES: add uuid, backfill, enforce NOT NULL + unique
    # ------------------------------------------------------------------
    op.add_column(
        "employees",
        sa.Column(
            "uuid",
            _uuid_type(),
            nullable=True,
        ),
    )

    employees = bind.execute(
        sa.text("SELECT id FROM employees WHERE uuid IS NULL")
    ).fetchall()
    for row in employees:
        bind.execute(
            sa.text("UPDATE employees SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )

    op.alter_column("employees", "uuid", nullable=False)
    op.create_index("ix_employees_uuid", "employees", ["uuid"], unique=True)

    # ------------------------------------------------------------------
    # 3) INSTITUTIONS: add uuid + institution_type, harden TIN rule
    # ------------------------------------------------------------------
    op.add_column(
        "institutions",
        sa.Column(
            "uuid",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.add_column(
        "institutions",
        sa.Column(
            "institution_type",
            sa.String(length=32),
            nullable=True,
        ),
    )

    institutions = bind.execute(
        sa.text("SELECT id FROM institutions WHERE uuid IS NULL")
    ).fetchall()
    for row in institutions:
        bind.execute(
            sa.text("UPDATE institutions SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )

    op.alter_column("institutions", "uuid", nullable=False)
    op.create_index(
        "ix_institutions_uuid",
        "institutions",
        ["uuid"],
        unique=True,
    )

    # Harden TIN: enforce 10 digits, starting with 0 (range 0000000000–0999999999)
    op.drop_constraint(
        "ck_institutions_tin_digits", "institutions", type_="check"
    )
    op.create_check_constraint(
        "ck_institutions_tin_digits",
        "institutions",
        "length(tin) = 10 AND tin >= '0000000000' AND tin <= '0999999999'",
    )

    # ------------------------------------------------------------------
    # 4) CLIENT_REGISTRATIONS: add uuid + institution_type + TIN rule
    # ------------------------------------------------------------------
    op.add_column(
        "client_registrations",
        sa.Column(
            "uuid",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.add_column(
        "client_registrations",
        sa.Column(
            "institution_type",
            sa.String(length=32),
            nullable=True,
        ),
    )

    regs = bind.execute(
        sa.text("SELECT id FROM client_registrations WHERE uuid IS NULL")
    ).fetchall()
    for row in regs:
        bind.execute(
            sa.text("UPDATE client_registrations SET uuid = :u WHERE id = :id"),
            {"u": str(uuid.uuid4()), "id": row.id},
        )

    op.alter_column("client_registrations", "uuid", nullable=False)
    op.create_index(
        "ix_client_registrations_uuid",
        "client_registrations",
        ["uuid"],
        unique=True,
    )

    op.create_check_constraint(
        "ck_client_registrations_tin_digits",
        "client_registrations",
        "length(tin) = 10 AND tin >= '0000000000' AND tin <= '0999999999'",
    )


def downgrade() -> None:
    # Reverse of upgrade – useful if you ever need to roll back.
    op.drop_constraint(
        "ck_client_registrations_tin_digits",
        "client_registrations",
        type_="check",
    )
    op.drop_index("ix_client_registrations_uuid", table_name="client_registrations")
    op.drop_column("client_registrations", "institution_type")
    op.drop_column("client_registrations", "uuid")

    op.drop_constraint(
        "ck_institutions_tin_digits",
        "institutions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_institutions_tin_digits",
        "institutions",
        "length(tin) = 10 AND tin >= '0000000000' AND tin <= '9999999999'",
    )
    op.drop_index("ix_institutions_uuid", table_name="institutions")
    op.drop_column("institutions", "institution_type")
    op.drop_column("institutions", "uuid")

    op.drop_index("ix_employees_uuid", table_name="employees")
    op.drop_column("employees", "uuid")

    op.drop_index("ix_users_uuid", table_name="users")
    op.drop_column("users", "uuid")
