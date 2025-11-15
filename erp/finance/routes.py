"""Legacy finance routes module.

Most finance-related views now live under :mod:`erp.finance` or
:mod:`erp.blueprints.finance`. This module is kept as a lightweight
placeholder so old imports don't break.
"""

from . import bp  # noqa: F401  (re-export blueprint for backwards compatibility)
