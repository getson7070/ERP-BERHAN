# celery_app.py
from celery import Celery
from app import create_app, db

# Create the Flask app (don’t start Socket.IO here, just build the context)
flask_app = create_app()

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    )
    # Use only modern lowercase config keys
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=app.config.get("CELERY_TIMEZONE", "UTC"),
        enable_utc=True,
    )

    class ContextTask(celery.Task):
        """Tasks run inside the Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Build Celery instance (but only if you actually run `celery -A celery_app.celery worker`)
celery = make_celery(flask_app)


@celery.task
def example_task(x, y):
    """A sample background task (can be removed/renamed)."""
    return x + y
