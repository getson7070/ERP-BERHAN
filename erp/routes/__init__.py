# erp/__init__.py
from .app import create_app

__all__ = ["create_app"]
# expose blueprints for easy import
