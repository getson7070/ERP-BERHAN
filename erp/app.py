import os

def _coerce_db_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg2" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

def create_app():
    app = Flask(__name__)

    raw_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    final_url = _coerce_db_url(raw_url)
    if not final_url:
        raise RuntimeError("No database URL found in env.")

    app.config["SQLALCHEMY_DATABASE_URI"] = final_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # If you use Flask-Limiter 3.x, don't pass storage_uri to init_app (see below)
    # app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI", "memory://"))

    init_extensions(app)
    # ... rest of your factory
    return app
