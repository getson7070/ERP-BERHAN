# erp/config.py
import os

def _as_bool(v: str | None, default=False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}

class BaseConfig:
    APP_ENV = os.getenv("APP_ENV", "production")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    # Database: accept either SQLALCHEMY_DATABASE_URI or DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Eager init check to avoid the Render crash you saw
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("Either 'SQLALCHEMY_DATABASE_URI' or 'DATABASE_URL' must be set.")

    # Cache
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # CORS
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    # Rate limit
    DEFAULT_RATE_LIMITS = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    FLASK_LIMITER_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI") or "memory://"

    # Brand
    BRAND_NAME = os.getenv("BRAND_NAME", "BERHAN")
    BRAND_PRIMARY = os.getenv("BRAND_PRIMARY", "#0d6efd")
    BRAND_ACCENT = os.getenv("BRAND_ACCENT", "#198754")

    # Login toggles (used by choose_login)
    ENABLE_CLIENT_LOGIN = _as_bool(os.getenv("ENABLE_CLIENT_LOGIN", "true"), True)
    ENABLE_EMPLOYEE_LOGIN = _as_bool(os.getenv("ENABLE_EMPLOYEE_LOGIN", "false"))
    ENABLE_ADMIN_LOGIN = _as_bool(os.getenv("ENABLE_ADMIN_LOGIN", "false"))
    ENABLE_WAREHOUSE = _as_bool(os.getenv("ENABLE_WAREHOUSE", "false"))

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS", "true"), True)
    MAIL_USE_SSL = _as_bool(os.getenv("MAIL_USE_SSL", "false"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")

class ProductionConfig(BaseConfig):
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True

def get_config() -> type[BaseConfig]:
    # Accept either FLASK_CONFIG="erp.config.ProductionConfig" or simple "production"
    fc = os.getenv("FLASK_CONFIG", "").strip()
    short = fc.rsplit(".", 1)[-1].lower() if fc else os.getenv("APP_ENV", "production").lower()
    if "dev" in short:
        return DevelopmentConfig
    return ProductionConfig
