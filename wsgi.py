# wsgi.py
# Important: eventlet must be monkey-patched BEFORE importing anything that might use stdlib concurrency.
import eventlet
eventlet.monkey_patch()

from erp.app import create_app

app = create_app()

if __name__ == "__main__":
    # For local dev only; Render uses gunicorn
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
