# revision identifiers, used by Alembic.
revision = ${repr(up_revision_id)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
