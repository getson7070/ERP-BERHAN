
from __future__ import annotations
import os

class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    TESTING = os.getenv("FLASK_TESTING", "0") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def validate_config(cfg: Config):
    is_prod = os.getenv("FLASK_ENV") == "production"
    if is_prod:
        if not cfg.SECRET_KEY or cfg.SECRET_KEY == "change-me-in-prod":
            raise RuntimeError("SECRET_KEY must be set in production")
        if not cfg.DATABASE_URL or cfg.DATABASE_URL.startswith("sqlite://"):
            raise RuntimeError("DATABASE_URL must be a real database in production")
