"""Telegram bot entry point.

The bot is optional and only enabled when the ``python-telegram-bot``
dependency is installed. Importing this module should not fail if the
dependency is missing so that the rest of the application and test suite
remain functional.
"""

from __future__ import annotations

import logging
import os

try:  # pragma: no cover - optional dependency
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.ext import Application, Defaults
    from . import handlers
except ImportError:  # pragma: no cover
    Update = ParseMode = Application = Defaults = None  # type: ignore
    handlers = None  # type: ignore

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the Telegram bot if available."""
    if Application is None or handlers is None:
        raise RuntimeError("telegram is not installed; bot is disabled")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    logging.basicConfig(level=logging.INFO)

    application = (
        Application.builder()
        .token(token)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )

    handlers.register(application)

    application.run_polling(timeout=120, allowed_updates=Update.ALL_TYPES)


__all__ = ["main"]

if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()


