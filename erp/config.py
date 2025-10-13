# erp/config.py
import os

class BaseConfig:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    # DB: accept either SQLALCHEMY_DATABASE_URI or DATABASE_URL
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or ""
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Cache
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # Limiter storage (prefer explicit, default to memory)
    FLASK_LIMITER_STORAGE_URI = (
        os.getenv("FLASK_LIMITER_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or "memory://"
    )
    DEFAULT_RATE_LIMITS = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")

    # SocketIO / Eventlet
    SOCKETIO_CORS = CORS_ORIGINS

    # Branding
    BRAND_NAME = os.getenv("BRAND_NAME", "Berhan Pharma")
    BRAND_TAGLINE = os.getenv("BRAND_TAGLINE", "Care to Every Shipment")
    BRAND_LOGO = os.getenv("BRAND_LOGO", "pictures/BERHAN-PHARMA-LOGO.jpg")

    # Entry template (home)
    ENTRY_TEMPLATE = os.getenv("ENTRY_TEMPLATE", "choose_login.html")

    # Feature toggles for logins
    ENABLE_CLIENT_LOGIN = os.getenv("ENABLE_CLIENT_LOGIN", "true").lower() == "true"
    ENABLE_EMPLOYEE_LOGIN = os.getenv("ENABLE_EMPLOYEE_LOGIN", "false").lower() == "true"
    ENABLE_ADMIN_LOGIN = os.getenv("ENABLE_ADMIN_LOGIN", "false").lower() == "true"


class ProductionConfig(BaseConfig):
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
