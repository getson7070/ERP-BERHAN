#!/usr/bin/env python3
"""Simple Celery queue monitor with email/Slack alerts."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

import requests
from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
THRESHOLD = int(os.environ.get("QUEUE_ALERT_THRESHOLD", "100"))
ALERT_EMAIL = os.environ.get("ALERT_EMAIL")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "localhost")

app = Celery(broker=BROKER_URL)


def _send_email(backlog: int) -> None:
    if not ALERT_EMAIL:
        return
    msg = EmailMessage()
    msg["Subject"] = "Celery backlog alert"
    msg["From"] = ALERT_EMAIL
    msg["To"] = ALERT_EMAIL
    msg.set_content(f"Queue backlog has reached {backlog} tasks")
    with smtplib.SMTP(SMTP_SERVER) as smtp:
        smtp.send_message(msg)


def _send_slack(backlog: int) -> None:
    if not SLACK_WEBHOOK:
        return
    requests.post(SLACK_WEBHOOK, json={"text": f"Celery backlog: {backlog} tasks"})


def main() -> None:
    inspector = app.control.inspect()
    active = inspector.active() or {}
    reserved = inspector.reserved() or {}
    backlog = sum(len(v) for v in active.values()) + sum(len(v) for v in reserved.values())
    if backlog > THRESHOLD:
        _send_email(backlog)
        _send_slack(backlog)


if __name__ == "__main__":
    main()
