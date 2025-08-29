import multiprocessing
import os
from prometheus_client import multiprocess

bind = "0.0.0.0:8000"
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.getenv("GUNICORN_THREADS", "1"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))

statsd_host = os.getenv("STATSD_HOST")
statsd_prefix = os.getenv("STATSD_PREFIX", "erp")
if statsd_host:
    statsd_port = os.getenv("STATSD_PORT", "8125")
    statsd_host = f"{statsd_host}:{statsd_port}"


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
