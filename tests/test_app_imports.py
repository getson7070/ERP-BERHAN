"""Import-time smoke checks for the application factory.

These tests ensure the core package can be imported in isolation. We previously
had NameError crashes (e.g., missing ``logging``/``Path`` imports) during
``flask db upgrade`` and Gunicorn startup. By asserting a clean import here, we
catch missing standard library imports before Docker builds or migrations fail.
"""

import importlib


def test_imports_are_resolved():
    """Import the top-level package and confirm create_app is reachable."""

    import erp

    # Reload to exercise module-level initialization.
    erp = importlib.reload(erp)

    assert hasattr(erp, "create_app")
    assert hasattr(erp, "LOGGER")
    assert hasattr(erp, "_dead_letter_handler")


def test_wsgi_entrypoint_loads():
    """Ensure the WSGI module imports cleanly for Gunicorn/Flask CLI flows."""

    wsgi = importlib.import_module("wsgi")

    assert getattr(wsgi, "app", None) is not None
    assert getattr(wsgi, "application", None) is wsgi.app

