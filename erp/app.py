"""Canonical production WSGI application.

Serve ``erp.app:app`` (or ``wsgi:application``) in all production deployments.
This ensures the full ERP app factory is used instead of any dev-only stubs.
"""

from . import create_app

app = create_app()
