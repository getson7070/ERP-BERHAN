"""Enrich client onboarding models with institution + approvals."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "8b2f4d7c3a10"
down_revision = "15c2d3e4f5ab"
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _has_col(insp, table: str, col: str) -> bool:
    return col in {c["name"] for c in insp.get_columns(table)}


def _has_index(insp, table: str, name: str) -> bool:
    return name in {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Institutions table ----------------------------------------------------
    if not _has_table(insp, "institutions"):
        op.create_table(
            "institutions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tin", sa.String(length=32), nullable=False),
            sa.Column("legal_name", sa.String(length=255), nullable=False),
            sa.Column("region", sa.String(length=128), nullable=True),
            sa.Column("zone", sa.String(length=128), nullable=True),
            sa.Column("city", sa.String(length=128), nullable=True),
            sa.Column("subcity", sa.String(length=128), nullable=True),
            sa.Column("woreda", sa.String(length=128), nullable=True),
            sa.Column("kebele", sa.String(length=128), nullable=True),
            sa.Column("street", sa.String(length=255), nullable=True),
            sa.Column("house_number", sa.String(length=64), nullable=True),
            sa.Column("gps_hint", sa.String(length=255), nullable=True),
            sa.Column("main_phone", sa.String(length=64), nullable=True),
            sa.Column("main_email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column(
                "org_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
        )
        op.create_index("ix_institutions_tin", "institutions", ["tin"])
        op.create_unique_constraint(
            "uq_institutions_org_tin", "institutions", ["org_id", "tin"]
        )

    # Client registrations --------------------------------------------------
    if _has_table(insp, "client_registrations"):
        columns_to_add = [
            ("institution_name", sa.Column("institution_name", sa.String(length=255), nullable=True)),
            ("contact_name", sa.Column("contact_name", sa.String(length=255), nullable=True)),
            ("contact_position", sa.Column("contact_position", sa.String(length=128), nullable=True)),
            ("phone", sa.Column("phone", sa.String(length=64), nullable=True)),
            ("tin", sa.Column("tin", sa.String(length=32), nullable=True)),
            ("region", sa.Column("region", sa.String(length=128), nullable=True)),
            ("zone", sa.Column("zone", sa.String(length=128), nullable=True)),
            ("city", sa.Column("city", sa.String(length=128), nullable=True)),
            ("subcity", sa.Column("subcity", sa.String(length=128), nullable=True)),
            ("woreda", sa.Column("woreda", sa.String(length=128), nullable=True)),
            ("kebele", sa.Column("kebele", sa.String(length=128), nullable=True)),
            ("street", sa.Column("street", sa.String(length=255), nullable=True)),
            ("house_number", sa.Column("house_number", sa.String(length=64), nullable=True)),
            ("gps_hint", sa.Column("gps_hint", sa.String(length=255), nullable=True)),
            ("notes", sa.Column("notes", sa.Text(), nullable=True)),
            ("password_hash", sa.Column("password_hash", sa.String(length=255), nullable=True)),
            (
                "decided_by",
                sa.Column(
                    "decided_by",
                    sa.Integer(),
                    sa.ForeignKey("users.id", ondelete="SET NULL"),
                    nullable=True,
                ),
            ),
            ("decision_notes", sa.Column("decision_notes", sa.Text(), nullable=True)),
        ]
        for name, column in columns_to_add:
            if not _has_col(insp, "client_registrations", name):
                op.add_column("client_registrations", column)

        if not _has_index(insp, "client_registrations", "ix_client_registrations_tin"):
            op.create_index("ix_client_registrations_tin", "client_registrations", ["tin"])
        if "uq_client_registrations_org_tin" not in {c["name"] for c in insp.get_unique_constraints("client_registrations")}:  # type: ignore[arg-type]
            try:
                op.create_unique_constraint(
                    "uq_client_registrations_org_tin",
                    "client_registrations",
                    ["org_id", "tin"],
                )
            except Exception:
                # Skip if data conflicts; admin can resolve and re-run
                pass

    # Client accounts -------------------------------------------------------
    if _has_table(insp, "client_accounts") and not _has_col(insp, "client_accounts", "institution_id"):
        op.add_column(
            "client_accounts",
            sa.Column(
                "institution_id",
                sa.Integer(),
                sa.ForeignKey("institutions.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index("ix_client_accounts_institution_id", "client_accounts", ["institution_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if _has_table(insp, "client_accounts") and _has_col(insp, "client_accounts", "institution_id"):
        op.drop_index("ix_client_accounts_institution_id", table_name="client_accounts")
        op.drop_column("client_accounts", "institution_id")

    if _has_table(insp, "client_registrations"):
        for name in [
            "decision_notes",
            "decided_by",
            "password_hash",
            "notes",
            "gps_hint",
            "house_number",
            "street",
            "kebele",
            "woreda",
            "subcity",
            "city",
            "zone",
            "region",
            "tin",
            "phone",
            "contact_position",
            "contact_name",
            "institution_name",
        ]:
            if _has_col(insp, "client_registrations", name):
                op.drop_column("client_registrations", name)
        if _has_index(insp, "client_registrations", "ix_client_registrations_tin"):
            op.drop_index("ix_client_registrations_tin", table_name="client_registrations")
        try:
            op.drop_constraint(
                "uq_client_registrations_org_tin", "client_registrations", type_="unique"
            )
        except Exception:
            pass

    if _has_table(insp, "institutions"):
        op.drop_index("ix_institutions_tin", table_name="institutions")
        try:
            op.drop_constraint("uq_institutions_org_tin", "institutions", type_="unique")
        except Exception:
            pass
        op.drop_table("institutions")
