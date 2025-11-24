"""Merge all heads (final).

WHY THIS EXISTS
---------------
This is a pure merge revision. It must list ONLY the actual heads that
exist immediately before this merge.

Previously it incorrectly included `d0b1b1c4f7a0` as a down_revision.
But that revision is NOT a head anymore (inventory was already merged
via `f4a5c6d7e8f9`). On a fresh DB this caused:

    KeyError: 'd0b1b1c4f7a0'

because Alembic tried to merge a non-head.

After this fix, the real heads are:
- 0f1a2b3c4d5e (geolocation)
- 1f2a3b4c5d6e (client auth)
- b4d7e6f9c0a1 (audit spine)

No schema changes are done here.
"""

from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision = "35aef64fca2d"
down_revision = ("0f1a2b3c4d5e", "1f2a3b4c5d6e", "b4d7e6f9c0a1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge only; no-op.
    pass


def downgrade() -> None:
    # Merge only; no-op.
    pass
