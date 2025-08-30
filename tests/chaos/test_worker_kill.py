import pytest
import subprocess  # nosec B404
import time


@pytest.mark.skip(reason="requires running Celery worker and system signals")
def test_kill_celery_worker():
    """Spawn a Celery worker and ensure it exits when killed."""
    proc = subprocess.Popen(
        [  # nosec
            "celery",
            "-A",
            "erp.celery_app",
            "worker",
            "--loglevel=INFO",
        ]
    )
    # give the worker a moment to start
    time.sleep(1)
    proc.terminate()
    proc.wait(timeout=5)
    assert proc.poll() is not None  # nosec B101
