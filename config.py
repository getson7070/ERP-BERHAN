import os

class Config:
    WTF_CSRF_ENABLED = True
    REMEMBER_COOKIE_HTTPONLY = True
    # Core
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF
    WTF_CSRF_TIME_LIMIT = None  # tokens do not expire during a session

    # CORS
    CORS_SUPPORTS_CREDENTIALS = True



