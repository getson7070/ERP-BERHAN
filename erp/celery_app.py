import os
from celery import Celery

def make_celery(app):
    broker = os.getenv("CELERY_BROKER_URL")
    backend = os.getenv("CELERY_RESULT_BACKEND", broker)

    celery = Celery(
        app.import_name,
        broker=broker,
        backend=backend,
        include=[],
    )
    # Copy Flask config into Celery namespace
    celery.conf.update(
        task_always_eager=not bool(broker),  # If no Redis yet, tasks run inline (dev)
        timezone="UTC",
        task_track_started=True,
        broker_connection_retry_on_startup=True,
    )

    # Run tasks with app context
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
