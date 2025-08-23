import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
FERNET_KEY = os.environ.get('FERNET_KEY', 'change-me')
DATABASE_URL = os.environ.get('DATABASE_URL', 'erp.db')
