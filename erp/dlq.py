"""
In-process "dead letter" storage with a simple handler.
"""
from __future__ import annotations

dead_letters: list = []

def send_to_dlq(message) -> None:
    dead_letters.append(message)