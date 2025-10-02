"""add core module tables (idempotent + sqlite-safe)"""

from alembic import op
import sqlalchemy as sa

revision = "7c9d0e1f2g3h"
down_revision = "c3d4e5f6g7h"  # keep whatever yours is now
branch_labels = None
depends_on = None


def _has_table(conn, name: str) -> bool:
    insp = sa.inspect(conn)
    try:
        return insp.has_table(name)
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # --- organizations -------------------------------------------------------
    if not _has_table(conn, "organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        # unique(name)
        if dialect == "sqlite":
            op.create_index("uq_organizations_name", "organizations", ["name"], unique=True)
        else:
            op.create_unique_constraint("uq_organizations_name", "organizations", ["name"])
    else:
        # Ensure unique on name exists without crashing if it already does
        if dialect == "sqlite":
            op.create_index("uq_organizations_name", "organizations", ["name"], unique=True)
        else:
            op.execute(sa.text(
                "DO $$ BEGIN "
                "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_organizations_name') THEN "
                "ALTER TABLE organizations ADD CONSTRAINT uq_organizations_name UNIQUE (name); "
                "END IF; END $$;"
            ))

    # TODO: repeat the same “exists” pattern for any *other* tables that this
    # migration originally created (e.g., departments, projects, etc).
    # Wrap each op.create_table(...) in an if-not-exists guard like above.


def downgrade() -> None:
    # Be conservative: drop unique/index then table if it exists.
    conn = op.get_bind()
    dialect = conn.dialect.name

    if _has_table(conn, "organizations"):
        if dialect == "sqlite":
            # SQLite: index name
            try:
                op.drop_index("uq_organizations_name", table_name="organizations")
            except Exception:
                pass
        else:
            try:
                op.drop_constraint("uq_organizations_name", "organizations", type_="unique")
            except Exception:
                pass
        op.drop_table("organizations")
