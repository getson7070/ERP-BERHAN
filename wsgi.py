"""Production WSGI entrypoint.

Deploy gunicorn/uwsgi against ``erp.app:app`` (or this wrapper) only.  This
keeps the production surface consistent and avoids accidentally loading
development scaffolding such as ``wsgi_phase1``.
"""

from erp.app import app

# Some WSGI hosts expect ``application``
application = app
