"""
Telegram plugin shim for tests.

Provides register() hook; real impl later.
"""

def register(app):
    """Register Telegram bot with Flask app."""
    setattr(app, "telegram_bot_registered", True)