"""Compat entry point for ``flask run``.

The application is initialised in :mod:`wsgi` to ensure a single
configuration path. This module merely exposes the already-created
``app`` for local development convenience.
"""

from wsgi import app

if __name__ == "__main__":
    app.run()
