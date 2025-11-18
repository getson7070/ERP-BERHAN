"""WSGI entrypoint for Gunicorn and Flask CLI commands."""

from erp import create_app

# Gunicorn expects an ``app`` object; some platforms look for ``application``.
app = create_app()
application = app

if __name__ == "__main__":  # pragma: no cover - manual local execution helper
    app.run(host="0.0.0.0", port=8000)
