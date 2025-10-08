# gunicorn.conf.py
from eventlet import monkey_patch
monkey_patch()  # ensures green thread monkey patching before workers import anything

bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = 1
preload_app = True  # import app in master so monkey_patch happens early enough
timeout = 120
loglevel = "info"
accesslog = "-"
errorlog = "-"
