import os
from datetime import timedelta

from erp.secrets import get_secret


class Config:
    _flask_secret_key = os.environ.get("FLASK_SECRET_KEY") or os.environ.get(
        "SECRET_KEY"
    )
    if not _flask_secret_key:
        raise RuntimeError("FLASK_SECRET_KEY/SECRET_KEY not set")
    SECRET_KEY = _flask_secret_key
    # Use a non-superuser account by default to enforce least privilege
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql://erp_app:erp_app@localhost:5432/erp?sslmode=require",
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    # Database connection pooling
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
    PREFERRED_URL_SCHEME = "https"
    JWT_SECRET = get_secret("JWT_SECRET")
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET not set")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_LIFETIME_MINUTES = int(os.environ.get("SESSION_LIFETIME_MINUTES", "30"))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_LIFETIME_MINUTES)
    WTF_CSRF_TIME_LIMIT = None

    ARGON2_TIME_COST = int(os.environ.get("ARGON2_TIME_COST", "3"))
    ARGON2_MEMORY_COST = int(os.environ.get("ARGON2_MEMORY_COST", "65536"))
    ARGON2_PARALLELISM = int(os.environ.get("ARGON2_PARALLELISM", "2"))

    OAUTH_CLIENT_ID = get_secret("OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET = get_secret("OAUTH_CLIENT_SECRET")
    OAUTH_AUTH_URL = os.environ.get("OAUTH_AUTH_URL")
    OAUTH_TOKEN_URL = os.environ.get("OAUTH_TOKEN_URL")
    OAUTH_USERINFO_URL = os.environ.get("OAUTH_USERINFO_URL")

    BABEL_DEFAULT_LOCALE = os.environ.get("BABEL_DEFAULT_LOCALE", "en")
    BABEL_SUPPORTED_LOCALES = os.environ.get("BABEL_SUPPORTED_LOCALES", "en,am").split(
        ","
    )
    LANGUAGES = {"en": "English", "am": "አማርኛ"}
    BABEL_DEFAULT_TIMEZONE = "UTC"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    API_TOKEN = get_secret("API_TOKEN")
    ACCOUNTING_URL = os.environ.get("ACCOUNTING_URL")
    PLUGIN_PATH = os.environ.get("PLUGIN_PATH", "plugins")
    PLUGIN_ALLOWLIST = (
        os.environ.get("PLUGIN_ALLOWLIST", "").split(",")
        if os.environ.get("PLUGIN_ALLOWLIST")
        else []
    )
    WEBHOOK_SECRET = get_secret("WEBHOOK_SECRET")
    S3_ENDPOINT = os.environ.get("S3_ENDPOINT")
    S3_BUCKET = os.environ.get("S3_BUCKET")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION")
    LOCK_THRESHOLD = int(os.environ.get("LOCK_THRESHOLD", "5"))
    LOCK_WINDOW = int(os.environ.get("LOCK_WINDOW", "300"))
    ACCOUNT_LOCK_SECONDS = int(os.environ.get("ACCOUNT_LOCK_SECONDS", "900"))
    MAX_BACKOFF = int(os.environ.get("MAX_BACKOFF", "60"))
    # --- Additional security, plugin, and support configuration ---
    # Enable encryption at rest (True/False). When True, the system should integrate with
    # database/disk encryption mechanisms provided by the deployment environment.
    ENCRYPTION_AT_REST_ENABLED = (
        os.environ.get("ENCRYPTION_AT_REST_ENABLED", "False").lower() == "true"
    )
    # Path to the encryption key or key management service identifier
    ENCRYPTION_KEY_PATH = os.environ.get(
        "ENCRYPTION_KEY_PATH", "/path/to/encryption/key"
    )
    # Enable multi-factor authentication for all users
    MFA_ENABLED = os.environ.get("MFA_ENABLED", "False").lower() == "true"
    # MFA provider (e.g., totp, sms, email)
    MFA_PROVIDER = os.environ.get("MFA_PROVIDER", "totp")
    # Issuer name for MFA tokens (used by authenticator apps)
    MFA_ISSUER = os.environ.get("MFA_ISSUER", "ERP-BERHAN")
    # Enable sandboxing for plugins to isolate third-party extensions
    PLUGIN_SANDBOX_ENABLED = (
        os.environ.get("PLUGIN_SANDBOX_ENABLED", "False").lower() == "true"
    )
    # URLs for support portal and community forum
    SUPPORT_PORTAL_URL = os.environ.get(
        "SUPPORT_PORTAL_URL", "https://support.example.com"
    )
    COMMUNITY_FORUM_URL = os.environ.get(
        "COMMUNITY_FORUM_URL", "https://community.example.com"
    )
    # Licensing and cost model configuration
    LICENSE_MODEL = os.environ.get("LICENSE_MODEL", "MIT")
    COST_MODEL_URL = os.environ.get("COST_MODEL_URL", "")


env = os.environ.get("ENV")
if env == "production":
    missing: list[str] = []
    insecure: list[str] = []

    default_vals = {"changeme", "secret", "password", ""}

    secret_key = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY")
    if not secret_key:
        missing.append("SECRET_KEY")
    elif secret_key in default_vals:
        insecure.append("SECRET_KEY")

    salt = os.environ.get("SECURITY_PASSWORD_SALT")
    if not salt:
        missing.append("SECURITY_PASSWORD_SALT")
    elif salt in default_vals:
        insecure.append("SECURITY_PASSWORD_SALT")

    jwt_secret = get_secret("JWT_SECRET")
    if not jwt_secret:
        missing.append("JWT_SECRET")
    elif jwt_secret in default_vals:
        insecure.append("JWT_SECRET")

    if Config.DATABASE_URL.startswith("postgresql://postgres"):
        missing.append("DATABASE_URL")
    if "localhost" in Config.DATABASE_URL:
        insecure.append("DATABASE_URL")

    redis_url = os.environ.get("REDIS_URL")
    if os.environ.get("USE_FAKE_REDIS") != "1":
        if not redis_url:
            missing.append("REDIS_URL")
        elif "localhost" in redis_url:
            insecure.append("REDIS_URL")

    if not os.environ.get("SENTRY_DSN"):
        missing.append("SENTRY_DSN")

    if insecure:
        raise RuntimeError(
            "Insecure default secrets detected: " + ", ".join(sorted(set(insecure)))
        )
    if missing:
        raise RuntimeError(
            "Missing required production secrets: " + ", ".join(sorted(set(missing)))
        )
