"""WSGI entry point for BERHAN ERP.

The factory in :mod:`erp` wires up database connections, background workers,
and security layers such as CSRF protection, rate limiting and a lightweight
Web Application Firewall (WAF).  This module merely exposes the created app so
it can be served by any WSGI server (Gunicorn, uWSGI, etc.) while keeping a
simple ``flask run`` path for local development.

Run the application locally with::

    flask run

or under Gunicorn::

    gunicorn app:app
"""

from erp import create_app

app = create_app()
app.config["TEMPLATES_AUTO_RELOAD"] = True  # handy in dev; disable in prod


if __name__ == "__main__":
    # The built-in server is for local testing only.  In production, deploy via
    # a hardened reverse proxy or platform such as Gunicorn behind a WAF.
    app.run()
