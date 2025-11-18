import os


def _is_production() -> bool:
    """Return True when the environment is explicitly marked as production."""

    env_flag = os.environ.get("FLASK_ENV") or os.environ.get("ENV")
    return (env_flag or "").lower() == "production"


def _resolve_secret_key() -> str:
    """Fetch the SECRET_KEY and block unsafe defaults in production deployments."""

    secret_key = os.environ.get("SECRET_KEY")
    if _is_production() and (not secret_key or secret_key == "change-me-in-prod"):
        raise RuntimeError("SECRET_KEY must be set to a non-default value in production")

    return secret_key or "change-me-in-prod"


def _resolve_database_uri() -> str:
    """Return the configured database URI, rejecting local sqlite defaults in prod."""

    database_uri = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    if _is_production() and database_uri.startswith("sqlite://"):
        raise RuntimeError("DATABASE_URL must point to a production-ready database")

    return database_uri

class Config:
    WTF_CSRF_ENABLED = True
    REMEMBER_COOKIE_HTTPONLY = True
    # Core
    SECRET_KEY = _resolve_secret_key()
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF
    WTF_CSRF_TIME_LIMIT = None  # tokens do not expire during a session

    # CORS
    CORS_SUPPORTS_CREDENTIALS = True



