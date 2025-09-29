"""
Safe Celery integration that doesn't run unless ENABLE_CELERY=true and CELERY_BROKER_URL is set.

- Avoids importing Celery at process import time when you don't need it.
- When enabled, it attaches app context to tasks.
- Uses new-style, lowercase Celery config keys to avoid the "Cannot mix new and old setting keys" crash.
"""
from __future__ import annotations
from typing import Optional
from celery import Celery

def init_celery(flask_app) -> Optional[Celery]:
    broker = flask_app.config.get("CELERY_BROKER_URL")
    if not broker:
        return None

    backend = flask_app.config.get("CELERY_RESULT_BACKEND")

    celery = Celery(flask_app.import_name, broker=broker, backend=backend)

    # New-style lowercase config only – prevents the crash seen in logs
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=flask_app.config.get("CELERY_TIMEZONE", "UTC"),
        enable_utc=True,
        # Add your queue/exchange config here as lowercase keys
    )

    class AppContextTask(celery.Task):
        """Make every task run inside the Flask app context."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = AppContextTask
    flask_app.extensions["celery"] = celery
    return celery
