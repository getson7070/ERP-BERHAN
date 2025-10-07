# erp/__init__.py
# Keep this file minimal to avoid circular imports and partial module state.

from .app import create_app

__all__ = ["create_app"]
