# erp/models/__init__.py
from erp.db import db  # the ONE shared instance

# re-export model classes without defining another db/Base here
try:
    from .user import *            # noqa
    from .employee import *        # noqa
    from .finance import *         # noqa
    from .idempotency import *     # noqa
    from .integration import *     # noqa
    from .recall import *          # noqa
    from .user_dashboard import *  # noqa
except Exception:
    pass
