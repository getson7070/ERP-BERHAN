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
ALERT_EMAIL = os.environ.get("ALERT_EMAIL")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "localhost")

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


if __name__ == "__main__":
    main()
