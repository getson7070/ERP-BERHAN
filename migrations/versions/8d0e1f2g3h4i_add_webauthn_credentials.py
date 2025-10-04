"""Add webauthn credentials table (idempotent / existence-aware)."""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "8d0e1f2g3h4i"
down_revision = "7c9d0e1f2g3h"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Respect current schema (works for PG & SQLite)
    schema = None
    table_name = "webauthn_credentials"

    # If the table already exists (e.g., created manually), skip creation
    try:
        exists = insp.has_table(table_name, schema=schema)
    except TypeError:
        # older SQLA signatures
        exists = insp.has_table(table_name)

    if exists:
        return

    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("credential_id", sa.String(length=512), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),  # maps to BYTEA on PG
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("credential_id", name="uq_webauthn_credentials_credential_id"),
        schema=schema,
    )

    # Helpful index for lookups
    op.create_index("ix_webauthn_credentials_user_id", table_name, ["user_id"], unique=False, schema=schema)
    op.create_index("ix_webauthn_credentials_org_id", table_name, ["org_id"], unique=False, schema=schema)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    schema = None
    table_name = "webauthn_credentials"

    try:
        exists = insp.has_table(table_name, schema=schema)
    except TypeError:
        exists = insp.has_table(table_name)

    if exists:
        # Drop indexes first (idempotent-ish: ignore if missing)
        try:
            op.drop_index("ix_webauthn_credentials_user_id", table_name=table_name, schema=schema)
        except Exception:
            pass
        try:
            op.drop_index("ix_webauthn_credentials_org_id", table_name=table_name, schema=schema)
        except Exception:
            pass

        op.drop_table(table_name, schema=schema)
