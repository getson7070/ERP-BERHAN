import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'erp.db')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = None
