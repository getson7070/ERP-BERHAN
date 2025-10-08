# wsgi.py
from erp.app import create_app

# Gunicorn looks for "wsgi:app"
app = create_app()

if __name__ == "__main__":
    app.run()
