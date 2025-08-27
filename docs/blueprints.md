# Blueprints

The application auto-discovers Flask blueprints exposed as a module-level `bp` under the `erp.routes`, `erp.blueprints`, and `plugins` packages.

```python
from flask import Blueprint

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
def index():
    ...
```

Any module following this pattern is registered automatically at startup. See `register_blueprints` in `erp/app.py` for implementation details.
