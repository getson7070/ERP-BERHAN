# erp/utils/retries.py
from __future__ import annotations
from tenacity import (
    retry, retry_if_exception_type, stop_after_attempt,
    wait_exponential_jitter
)

class ExternalError(Exception):
    """Wrap external-call failures so retry policy stays simple."""
    pass

retry_external = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(0.5, 3.0),  # 0.5s..3s with jitter
    retry=retry_if_exception_type(ExternalError),
)
