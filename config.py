import json
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
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # CSRF
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour token validity
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_HEADERS = ("X-CSRFToken", "X-CSRF-Token")

    # CORS
    CORS_SUPPORTS_CREDENTIALS = True

    # Telegram / bot integration
    TELEGRAM_BOTS_JSON = os.getenv("TELEGRAM_BOTS_JSON", "")
    TELEGRAM_DEFAULT_BOT = os.getenv("TELEGRAM_DEFAULT_BOT", "erpbot")
    TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_SCOPES_JSON = os.getenv("TELEGRAM_BOT_SCOPES_JSON", "{}")
    BOT_FALLBACK_EMAILS = tuple(
        addr.strip()
        for addr in os.getenv("BOT_FALLBACK_EMAILS", "").split(",")
        if addr.strip()
    )

    # Resolved bot maps (class attribute so Flask picks it up during config load)
    TELEGRAM_BOTS = (
        json.loads(TELEGRAM_BOTS_JSON)
        if TELEGRAM_BOTS_JSON
        else ({TELEGRAM_DEFAULT_BOT: TELEGRAM_BOT_TOKEN} if TELEGRAM_BOT_TOKEN else {})
    )
    TELEGRAM_BOT_SCOPES = (
        json.loads(TELEGRAM_BOT_SCOPES_JSON)
        if TELEGRAM_BOT_SCOPES_JSON
        else {}
    )

    # Authentication / MFA
    # Roles listed here must complete MFA before login and while performing
    # privileged actions such as approvals, role changes, or financial posting.
    # Values are normalized to lowercase during enforcement.
    MFA_REQUIRED_ROLES = (
        "admin",
        "management",
        "supervisor",
    )



