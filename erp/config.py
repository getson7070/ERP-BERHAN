# erp/config.py
import os

class BaseConfig:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    RATELIMIT_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    DEFAULT_RATE_LIMITS = [s.strip() for s in os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second").split(";") if s.strip()]

    # Feature toggles
    ENABLE_CLIENT_LOGIN = os.getenv("ENABLE_CLIENT_LOGIN", "false").lower() == "true"
    ENABLE_EMPLOYEE_LOGIN = os.getenv("ENABLE_EMPLOYEE_LOGIN", "false").lower() == "true"
    ENABLE_ADMIN_LOGIN = os.getenv("ENABLE_ADMIN_LOGIN", "false").lower() == "true"

    # Entry template (landing)
    ENTRY_TEMPLATE = os.getenv("ENTRY_TEMPLATE", "choose_login.html")

class ProductionConfig(BaseConfig):
    ENV = "production"
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True


# --- Security hardening (auto) ---
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
WTF_CSRF_ENABLED = True
