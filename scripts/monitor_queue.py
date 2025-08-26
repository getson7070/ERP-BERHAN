"""Print Celery queue backlog size."""
import os
import time
import redis
from prometheus_client import Gauge, start_http_server

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUEUE = os.environ.get("CELERY_QUEUE", "celery")
METRIC = Gauge('queue_backlog', 'Queue backlog size')


def main() -> None:
    start_http_server(9419)
    r = redis.Redis.from_url(REDIS_URL)
    while True:
        size = r.llen(QUEUE)
        METRIC.set(size)
        print(f"Queue '{QUEUE}' backlog: {size}")
        time.sleep(5)

if __name__ == '__main__':
    main()
