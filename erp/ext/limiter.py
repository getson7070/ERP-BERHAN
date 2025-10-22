
import os

def _noop(*args, **kwargs):
    class Noop:
        def init_app(self, app):
            app.logger.warning("Limiter not installed; skipping.")
    return Noop()

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    _HAVE_LIMITER = True
except Exception:
    _HAVE_LIMITER = False
    Limiter = None
    get_remote_address = None

limiter = _noop()

def configure_rate_limits(app):
    """Configure limiter if installed; otherwise keep no-op."""
    global limiter
    if not _HAVE_LIMITER:
        limiter = _noop()
        return

    enabled = os.getenv("PHASE1_ENABLE_LIMITER", "true").lower() in {"1","true","yes","on"}
    if not enabled:
        limiter = _noop()
        return

    default_limits = os.getenv("PHASE1_RATE_LIMITS", "200 per minute")
    limits = [s.strip() for s in default_limits.split(";") if s.strip()]
    storage_uri = os.getenv("REDIS_URL", None)

    if storage_uri:
        limiter = Limiter(key_func=get_remote_address, default_limits=limits, storage_uri=storage_uri)
    else:
        limiter = Limiter(key_func=get_remote_address, default_limits=limits)  # in-memory fallback
