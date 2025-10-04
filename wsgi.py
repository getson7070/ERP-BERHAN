# wsgi.py — keep this file tiny and do monkey-patching FIRST
import eventlet
eventlet.monkey_patch()  # must happen before importing anything else

from erp.app import create_app  # noqa: E402 (import after patching is intentional)
app = create_app()
