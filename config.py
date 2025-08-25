import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'erp.db')
    PREFERRED_URL_SCHEME = 'https'
    TOTP_ISSUER = os.environ.get('TOTP_ISSUER', 'ERP-BERHAN')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_LIFETIME_MINUTES = int(os.environ.get('SESSION_LIFETIME_MINUTES', '30'))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_LIFETIME_MINUTES)
    WTF_CSRF_TIME_LIMIT = None
