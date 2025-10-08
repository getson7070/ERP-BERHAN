# erp/routes/__init__.py
from .auth import auth_bp
from .api import api_bp
from .main import bp as main_bp

__all__ = ["auth_bp", "api_bp", "main_bp"]
