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
    TELEGRAM_WEBHOOK_REQUIRE_SECRET = (
        os.getenv("TELEGRAM_WEBHOOK_REQUIRE_SECRET", "true").lower() != "false"
    )
    TELEGRAM_REQUIRE_ACTIVE_SESSION = (
        os.getenv("TELEGRAM_REQUIRE_ACTIVE_SESSION", "false").lower() == "true"
    )
    TELEGRAM_SESSION_MAX_AGE_SECONDS = int(os.getenv("TELEGRAM_SESSION_MAX_AGE_SECONDS", "7200"))
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_SCOPES_JSON = os.getenv("TELEGRAM_BOT_SCOPES_JSON", "{}")
    TELEGRAM_ALLOWED_CHAT_IDS_JSON = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS_JSON", "{}")
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
    TELEGRAM_ALLOWED_CHAT_IDS = (
        json.loads(TELEGRAM_ALLOWED_CHAT_IDS_JSON)
        if TELEGRAM_ALLOWED_CHAT_IDS_JSON
        else {}
    )

    # Support / Help Center defaults
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@example.com")
    SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "+1 (234) 567-890")
    SUPPORT_HOURS = os.getenv("SUPPORT_HOURS", "Mon–Fri, 9am–6pm local time")
    SUPPORT_RESPONSE_SLA = os.getenv("SUPPORT_RESPONSE_SLA", "We reply within one business day")
    HELP_SYSTEM_STATUS = (
        {
            "label": "Core platform",
            "status": "operational",
            "note": "APIs and dashboards are healthy",
        },
        {
            "label": "Automations & bots",
            "status": "operational",
            "note": "Telegram + workflow jobs are healthy",
        },
        {
            "label": "Planned maintenance",
            "status": "info",
            "note": "Planned maintenance will be announced in-app",
        },
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

    # Endpoints that should bypass the privileged MFA guard. Auth flows and
    # health checks stay reachable to avoid lockouts while enforcing MFA for
    # sensitive modules.
    MFA_GUARD_EXEMPT_ENDPOINTS = (
        "auth.login",
        "auth.register",
        "auth.client_register",
        "auth.logout",
        "healthz",
        "static",
    )



