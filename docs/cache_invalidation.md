# Cache Invalidation Rules

List views for CRM and inventory use Redis caching. Keys follow the pattern `<module>:<org_id>`.

When records change, invalidate with:
```
from erp.cache import cache_invalidate
cache_invalidate(f"<module>:{org_id}")
```
This keeps cached data consistent after writes.
