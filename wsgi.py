"""WSGI entrypoint for ERP-BERHAN."""
# eventlet must be monkey-patched before other imports if used
try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

from ERP-BERHAN-main import create_app  # adjust if your factory name differs

app = create_app()
