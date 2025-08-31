"""add compliance tables for part 11/gmp"""

from alembic import op
import sqlalchemy as sa

revision = "e6f7g8h9i0a"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "electronic_signatures",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("intent", sa.String(length=255), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64)),
        sa.Column("signature_hash", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "batch_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lot_number", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "non_conformances",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "batch_record_id",
            sa.Integer,
            sa.ForeignKey("batch_records.id"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="open"
        ),
    )


def downgrade():
    op.drop_table("non_conformances")
    op.drop_table("batch_records")
    op.drop_table("electronic_signatures")
