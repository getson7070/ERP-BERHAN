import os

class Config:
    # IMPORTANT: set in Render env too, but we also provide a sane default
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-please-very-random")
    WTF_CSRF_ENABLED = True

    # Database (Render provides DATABASE_URL). SQLAlchemy 2.x friendly.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Rate limiting storage (optional). No Redis until you say so.
    RATELIMIT_ENABLED = False

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

def get_config():
    return Config
