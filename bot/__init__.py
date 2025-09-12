import logging
import os

try:  # pragma: no cover - optional dependency
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.ext import Application, Defaults
except ImportError:  # pragma: no cover - telegram not installed
    Update = ParseMode = Application = Defaults = None  # type: ignore[assignment]

from . import handlers

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the Telegram bot."""
    if Application is None:
        raise RuntimeError("python-telegram-bot is not installed")

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
