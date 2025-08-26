"""Minimal Slack bot interface for notifications."""
import os
import requests

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')


def send_message(text: str) -> None:
    if not SLACK_WEBHOOK:
        return
    try:
        requests.post(SLACK_WEBHOOK, json={'text': text}, timeout=5)
    except requests.RequestException:
        pass
