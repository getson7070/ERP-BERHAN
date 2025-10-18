# erp/models/__init__.py
from erp.db import db  # single shared SQLAlchemy instance

# Import all model modules so SQLAlchemy registers tables once
from .user import *          # noqa: F401,F403
from .employee import *      # noqa: F401,F403
from .finance import *       # noqa: F401,F403
from .idempotency import *   # noqa: F401,F403
from .integration import *   # noqa: F401,F403
from .recall import *        # noqa: F401,F403
from .user_dashboard import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith('_')]