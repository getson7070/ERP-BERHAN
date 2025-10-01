# erp/app.py
import os

def _coerce_db_url(url: str | None) -> str | None:
    if not url:
        return None
    # accept postgres:// and upgrade to SQLAlchemy's expected dialect
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg2" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    # ensure sslmode=require if not present
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # Read DB URL from either SQLALCHEMY_DATABASE_URI or (fallback) DATABASE_URL
    raw_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    coerced = _coerce_db_url(raw_url)
    if not coerced:
        # last-ditch: raise a clear error before extensions initialize
        raise RuntimeError(
            "No database URL found. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = coerced
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # ... now it’s safe to init extensions
    init_extensions(app)
    # ...
    return app
