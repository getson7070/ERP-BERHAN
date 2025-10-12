# erp/config.py
import os

class BaseConfig:
    APP_ENV = os.getenv("APP_ENV", "production")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    FLASK_LIMITER_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"

class ProductionConfig(BaseConfig):
    ENV = "production"
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
