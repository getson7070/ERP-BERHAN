"""Measure request throughput for an endpoint using timeit."""

import os
import timeit
import requests

TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:5000/")
REQUESTS = int(os.environ.get("BENCH_REQUESTS", "100"))


def _hit():
    requests.get(TARGET_URL, timeout=5)


def main() -> None:
    duration = timeit.timeit(_hit, number=REQUESTS)
    rps = REQUESTS / duration if duration else 0
    print(f"Sent {REQUESTS} requests in {duration:.2f}s ({rps:.2f} req/s)")


if __name__ == "__main__":
    main()


