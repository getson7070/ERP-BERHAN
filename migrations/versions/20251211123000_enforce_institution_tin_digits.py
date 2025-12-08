"""enforce institution tin digits

Revision ID: 20251211123000
Revises: 20251209120000
Create Date: 2025-12-11 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251211123000"
down_revision = "20251209120000"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "ck_institutions_tin_digits",
        "institutions",
        "length(tin) = 10 AND tin >= '0000000000' AND tin <= '9999999999'",
    )


def downgrade():
    op.drop_constraint("ck_institutions_tin_digits", "institutions", type_="check")
