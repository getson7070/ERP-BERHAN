from erp.app import create_app

app = create_app()

# For local dev: `gunicorn -c gunicorn.conf.py wsgi:app`
