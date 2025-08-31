#!/usr/bin/env python3
"""Simple Celery queue monitor with email/Slack alerts."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

import requests  # type: ignore[import-untyped]
from celery import Celery
from db import redis_client

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
THRESHOLD = int(os.environ.get("QUEUE_ALERT_THRESHOLD", "100"))
DLQ_THRESHOLD = int(os.environ.get("DEAD_LETTER_THRESHOLD", "0"))
ERROR_500_THRESHOLD = int(os.environ.get("ERROR_500_THRESHOLD", "0"))
ERROR_429_THRESHOLD = int(os.environ.get("ERROR_429_THRESHOLD", "0"))
ALERT_EMAIL = os.environ.get("ALERT_EMAIL")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "localhost")
HEALTH_URL = os.environ.get("HEALTH_URL", "http://web:8000/healthz")
METRICS_URL = os.environ.get("METRICS_URL", "http://web:8000/metrics")

app = Celery(broker=BROKER_URL)


def _send_email(message: str, subject: str) -> None:
    if not ALERT_EMAIL:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL
    msg["To"] = ALERT_EMAIL
    msg.set_content(message)
    with smtplib.SMTP(SMTP_SERVER) as smtp:
        smtp.send_message(msg)


def _send_slack(message: str) -> None:
    if not SLACK_WEBHOOK:
        return
    requests.post(SLACK_WEBHOOK, json={"text": message})


def main() -> None:
    # Uptime check
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code != 200:
            msg = f"Health check failed with status {r.status_code}"
            _send_email(msg, "Health check alert")
            _send_slack(msg)
    except Exception as exc:  # pragma: no cover - network failure
        msg = f"Health check error: {exc}"
        _send_email(msg, "Health check alert")
        _send_slack(msg)

    # Queue backlog and DLQ size
    inspector = app.control.inspect()
    active = inspector.active() or {}
    reserved = inspector.reserved() or {}
    backlog = sum(len(v) for v in active.values()) + sum(
        len(v) for v in reserved.values()
    )
    if backlog > THRESHOLD:
        msg = f"Celery backlog has reached {backlog} tasks"
        _send_email(msg, "Celery backlog alert")
        _send_slack(msg)
    dlq_size = redis_client.llen("dead_letter")
    if dlq_size > DLQ_THRESHOLD:
        msg = f"Dead letter queue has {dlq_size} entries"
        _send_email(msg, "Dead letter queue alert")
        _send_slack(msg)

    # Error rate alerts from metrics
    try:
        metrics = requests.get(METRICS_URL, timeout=5).text.splitlines()
        errors_500 = next(
            (
                int(line.split()[1])
                for line in metrics
                if 'http_requests_total' in line and 'status="500"' in line
            ),
            0,
        )
        errors_429 = next(
            (
                int(line.split()[1])
                for line in metrics
                if 'http_requests_total' in line and 'status="429"' in line
            ),
            0,
        )
        if errors_500 > ERROR_500_THRESHOLD:
            msg = f"5xx errors exceeded threshold: {errors_500}"
            _send_email(msg, "5xx error alert")
            _send_slack(msg)
        if errors_429 > ERROR_429_THRESHOLD:
            msg = f"429 errors exceeded threshold: {errors_429}"
            _send_email(msg, "429 error alert")
            _send_slack(msg)
    except Exception as exc:  # pragma: no cover - metrics fetch failure
        msg = f"Metrics check error: {exc}"
        _send_email(msg, "Metrics check alert")
        _send_slack(msg)


if __name__ == "__main__":
    main()
