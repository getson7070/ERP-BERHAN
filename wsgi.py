# gunicorn.conf.py

# Monkey-patch as early as possible (gunicorn loads this file before workers)
import eventlet
eventlet.monkey_patch()

bind = "0.0.0.0:10000"
workers = 1
worker_class = "eventlet"
timeout = 120
loglevel = "info"

def pre_fork(server, worker):
    # Safety net: ensure patching even if something imported too early
    import eventlet
    eventlet.monkey_patch()
