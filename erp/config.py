# erp/config.py
import os
from pathlib import Path

def _normalize_db_uri(uri: str | None) -> str | None:
    if not uri:
        return None
    # SQLAlchemy requires postgresql://
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # Try several common envs, then fall back to a safe local sqlite DB
    SQLALCHEMY_DATABASE_URI = _normalize_db_uri(
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRESQL_URL")
    )
    if not SQLALCHEMY_DATABASE_URI:
        instance_dir = Path(os.getenv("INSTANCE_PATH", "instance"))
        instance_dir.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'app.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Rate limiting / Redis
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI")  # optional
    REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    SOCKETIO_MESSAGE_QUEUE = os.getenv("SOCKETIO_MESSAGE_QUEUE") or REDIS_URL

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Branding
    BRAND_NAME = os.getenv("BRAND_NAME", "BERHAN")
    BRAND_LOGO_PATH = os.getenv("BRAND_LOGO_PATH", "pictures/BERHAN-PHARMA-LOGO.jpg")
    BRAND_PRIMARY = os.getenv("BRAND_PRIMARY", "#1e88e5")
    BRAND_ACCENT = os.getenv("BRAND_ACCENT", "#00acc1")
