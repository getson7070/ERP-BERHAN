try:
    from celery import Celery
except Exception:
    Celery = None  # type: ignore

class _FakeTask:
    def __init__(self, f):
        self.f = f
    def delay(self, *a, **k):
        return self.f(*a, **k)
    def __call__(self, *a, **k):
        return self.f(*a, **k)

def make_celery(name="erp"):
    if Celery is None:
        class _FakeCelery:
            def task(self, *dargs, **dkwargs):
                def deco(f): return _FakeTask(f)
                return deco
        return _FakeCelery()
    app = Celery(name, broker="memory://", backend="rpc://")
    app.conf.task_always_eager = True
    return app

celery_app = make_celery()
