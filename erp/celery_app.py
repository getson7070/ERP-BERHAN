from celery import Celery


def make_celery(app) -> Celery:
    celery = Celery(app.import_name)
    celery.conf.update(app.config)

    def _register_tasks() -> None:
        # register tasks here if needed
        pass

    @celery.task
    def ping() -> str:
        return "pong"

    _register_tasks()
    return celery


