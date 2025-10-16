from flask import Flask
from datetime import timedelta

def init_app(app: Flask):
    # sensible defaults for prod-like performance
    app.config.setdefault("JSONIFY_PRETTYPRINT_REGULAR", False)
    app.config.setdefault("SEND_FILE_MAX_AGE_DEFAULT", timedelta(hours=1))
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 1800,
    })
    # simple gzip if using Proxy (Render/NGINX can also gzip)
    try:
        from flask_compress import Compress
        Compress(app)
    except Exception:
        pass
