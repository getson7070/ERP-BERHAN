"""merge heads 2025-10-03

Revision ID: 4879f87e41ba
Revises: 20251003_fix_kpi_sales_mv, bba086713f12
Create Date: 2025-10-03 11:32:04.587252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4879f87e41ba'
down_revision: Union[str, Sequence[str], None] = ('20251003_fix_kpi_sales_mv', 'bba086713f12')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
