"""Simple HTTP benchmark tool for ERP-BERHAN.

This script issues a number of concurrent GET requests against the target
URL and reports the average requests per second. Use it to gauge the effect
of tuning connection pools or scaling out pods.
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor

TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:5000/")
CONCURRENCY = int(os.environ.get("BENCH_CONCURRENCY", "10"))
REQUESTS = int(os.environ.get("BENCH_REQUESTS", "100"))

def _hit(url: str) -> None:
    requests.get(url, timeout=5)

def main() -> None:
    start = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as exc:
        for _ in range(REQUESTS):
            exc.submit(_hit, TARGET_URL)
    duration = time.time() - start
    rps = REQUESTS / duration if duration else 0
    print(f"Sent {REQUESTS} requests in {duration:.2f}s ({rps:.2f} req/s)")

if __name__ == "__main__":
    main()
