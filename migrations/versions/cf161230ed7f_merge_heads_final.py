"""merge heads final

Revision ID: cf161230ed7f
Revises: d1b125e62d70, 4879f87e41ba
Create Date: 2025-10-03 15:34:49.342235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf161230ed7f'
down_revision: Union[str, Sequence[str], None] = ('d1b125e62d70', '4879f87e41ba')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
