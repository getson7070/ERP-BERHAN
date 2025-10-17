import multiprocessing, os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:10000")
workers = int(os.getenv("WEB_CONCURRENCY", str(multiprocessing.cpu_count() * 2 + 1)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "eventlet")
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "2000"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"

def post_worker_init(worker):
    # Prometheus multiprocess for Gunicorn
    os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prom")
    os.makedirs("/tmp/prom", exist_ok=True)
