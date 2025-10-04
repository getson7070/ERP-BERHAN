import os

def _env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")

class Settings:
    # Environment
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Progressive features (flip later without code changes)
    ENABLE_SOCKETIO = _env_bool("ENABLE_SOCKETIO", True)
    ENABLE_OBSERVABILITY = _env_bool("ENABLE_OBSERVABILITY", False)
    ENABLE_CELERY = _env_bool("ENABLE_CELERY", False)  # placeholder for future
    MIGRATE_ON_STARTUP = _env_bool("MIGRATE_ON_STARTUP", False)

    # Realtime
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE")  # eventlet|gevent|threading|None
    SOCKETIO_MESSAGE_QUEUE = os.getenv("SOCKETIO_MESSAGE_QUEUE")  # e.g., redis://host:6379/0

    # Observability
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
