<<<< HEAD
# erp/models/__init__.py
from erp.db import db  # the ONE shared instance
=======
﻿# erp/models/__init__.py
# Re-export models here so `from erp.models import X` works everywhere.
from erp.extensions import db
from .user import User, DeviceAuthorization, DataLineage  # existing models
from .user_dashboard import UserDashboard                  # existing model
from .employee import Employee                             # NEW
>>>>>>> chore/phase1-upgrade-20251017-1848

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
