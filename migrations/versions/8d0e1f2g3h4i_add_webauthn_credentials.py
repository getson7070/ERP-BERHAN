"""add webauthn credentials table (idempotent / PG+SQLite safe)"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "8d0e1f2g3h4i"          # <-- keep this exactly as in your repo
down_revision = "7c9d0e1f2g3h"     # <-- matches your history
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite: only create if missing
        if not insp.has_table("webauthn_credentials"):
            op.create_table(
                "webauthn_credentials",
                sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
                sa.Column("user_id", sa.Integer, nullable=False),
                sa.Column("org_id", sa.Integer, nullable=False),
                sa.Column("credential_id", sa.String(512), nullable=False, unique=True),
                sa.Column("public_key", sa.LargeBinary, nullable=False),
                sa.Column("sign_count", sa.Integer, nullable=False, server_default="0"),
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    nullable=False,
                ),
                # FKs are no-ops unless you’ve enabled PRAGMA foreign_keys
            )
        return

    if dialect == "postgresql":
        # Postgres: guard with to_regclass() and use proper types/defaults
        op.execute(sa.text("""
        DO $plpgsql$
        BEGIN
          IF to_regclass('webauthn_credentials') IS NULL THEN
            CREATE TABLE webauthn_credentials (
              id            SERIAL PRIMARY KEY,
              user_id       INTEGER NOT NULL REFERENCES users(id),
              org_id        INTEGER NOT NULL REFERENCES organizations(id),
              credential_id VARCHAR(512) NOT NULL UNIQUE,
              public_key    BYTEA NOT NULL,
              sign_count    INTEGER NOT NULL DEFAULT 0,
              created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
            );
          ELSE
            RAISE NOTICE $$webauthn_credentials already exists; skipping creation$$;
          END IF;
        END
        $plpgsql$;
        """))
        return


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    if dialect == "sqlite":
        if insp.has_table("webauthn_credentials"):
            op.drop_table("webauthn_credentials")
        return

    if dialect == "postgresql":
        op.execute(sa.text("DROP TABLE IF EXISTS webauthn_credentials CASCADE"))
        return
