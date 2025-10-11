"""add core module tables (idempotent + sqlite-safe)"""

from alembic import op
import sqlalchemy as sa

revision = "7c9d0e1f2g3h"
down_revision = "c3d4e5f6g7h"  # keep whatever yours is now
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)

def _unique_names(insp, table: str) -> set[str]:
    try:
        return {uc["name"] for uc in insp.get_unique_constraints(table)}
    except Exception:
        return set()

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- organizations -------------------------------------------------------
    if not _has_table(insp, "organizations"):
        # Create the table if missing (no constraint inside CREATE to avoid replays)
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
        )

    # Ensure uniqueness on name regardless of prior state
    uqs = _unique_names(insp, "organizations")
    if "uq_organizations_name" not in uqs:
        # Prefer a named UNIQUE constraint (portable)
        op.create_unique_constraint("uq_organizations_name", "organizations", ["name"])

    # NOTE: if you previously created a UNIQUE index instead of a constraint,
    # keep both guards (constraint + index) or remove the index to avoid duplication:
    # existing = {i['name'] for i in insp.get_indexes('organizations')}
    # if 'uq_organizations_name' not in existing:
    #     op.create_index('uq_organizations_name', 'organizations', ['name'], unique=True)

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Drop uniqueness first (guarded)
    uqs = _unique_names(insp, "organizations")
    if "uq_organizations_name" in uqs:
        op.drop_constraint("uq_organizations_name", "organizations", type_="unique")

    if _has_table(insp, "organizations"):
        op.drop_table("organizations")
