class _Celery:
    def task(self, fn=None, **opts):
        def decorator(f):
            # give tests a .run attribute like real Celery tasks
            f.run = f
            return f
        return decorator if fn is None else decorator(fn)

celery = _Celery()
