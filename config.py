import os
import secrets
import json
from datetime import timedelta

from erp.secrets import get_secret


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get(
        "FLASK_SECRET_KEY", secrets.token_hex(16)
    )
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/erp"
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
    _default_secret = get_secret("JWT_SECRET") or secrets.token_hex(32)
    JWT_SECRETS = json.loads(
        get_secret("JWT_SECRETS") or json.dumps({"v1": _default_secret})
    )
    JWT_SECRET_ID = get_secret("JWT_SECRET_ID") or "v1"
    JWT_SECRET = JWT_SECRETS[JWT_SECRET_ID]
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
    LANGUAGES = BABEL_SUPPORTED_LOCALES
    BABEL_DEFAULT_TIMEZONE = "UTC"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    API_TOKEN = get_secret("API_TOKEN")
    ACCOUNTING_URL = os.environ.get("ACCOUNTING_URL")
    PLUGIN_PATH = os.environ.get("PLUGIN_PATH", "plugins")
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
