# wsgi.py
import eventlet
eventlet.monkey_patch(all=True)

from erp.app import create_app, socketio  # noqa: E402

app = create_app()

# Optional: allow `gunicorn wsgi:app` and `socketio.run()` locally
if __name__ == "__main__":
    # Local dev runner (not used on Render)
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
