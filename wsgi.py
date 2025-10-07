# wsgi.py
import eventlet
eventlet.monkey_patch()  # must be FIRST when using eventlet workers

from erp.app import create_app
app = create_app()

if __name__ == "__main__":
    # Local dev only; Render uses gunicorn
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
