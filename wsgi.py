# wsgi.py
# ── IMPORTANT: monkey-patch BEFORE any other imports ───────────────────────────
import eventlet
eventlet.monkey_patch()

from erp.app import create_app  # no other imports above this line

# Gunicorn will import this `app`
app = create_app()

# Optional local run (not used on Render)
if __name__ == "__main__":
    # Running via `python wsgi.py` for local debugging
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5000, app, use_reloader=True)
