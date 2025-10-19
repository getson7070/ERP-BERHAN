"""add idempotency_keys table"""

from alembic import op
import sqlalchemy as sa

# Set to your current head revision ID before generating:
revision = "a1b2c3d4e5f6"
down_revision = ''
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("endpoint", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_idem_key", "idempotency_keys", ["key"])
    op.create_index("ix_idem_endpoint", "idempotency_keys", ["endpoint"])
    op.create_index("ix_idem_created_at", "idempotency_keys", ["created_at"])

def downgrade():
    op.drop_index("ix_idem_created_at", table_name="idempotency_keys")
    op.drop_index("ix_idem_endpoint", table_name="idempotency_keys")
    op.drop_constraint("uq_idem_key", "idempotency_keys", type_="unique")
    op.drop_table("idempotency_keys")




