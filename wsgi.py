# wsgi.py — resilient entrypoint
def _load():
    try:
        from erp.app import create_app
        return create_app()
    except Exception:
        pass
    try:
        from erp import create_app
        return create_app()
    except Exception:
        pass
    try:
        from erp.app import app as flask_app
        return flask_app
    except Exception as e:
        raise RuntimeError("No application factory or app object found") from e

app = _load()
