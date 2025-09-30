from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

# These are imported by other modules (e.g. routes) before app exists.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
oauth = OAuth()

__all__ = ["limiter", "oauth"]
