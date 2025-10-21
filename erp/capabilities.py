def _has_eventlet() -> bool:
    try:
        import eventlet  # noqa: F401
        return True
    except Exception:
        return False

def choose_async_mode(settings) -> str:
    """
    Respect explicit env; otherwise prefer eventlet if present, then fallback to threading.
    """
    raw = settings.SOCKETIO_ASYNC_MODE
    allowed = {None, "eventlet", "gevent", "threading"}
    if raw not in allowed:
        raw = None

    if raw in (None, "eventlet"):
        return "eventlet" if _has_eventlet() else "threading"
    return raw

def maybe_init_sentry(settings):
    if not (settings.ENABLE_OBSERVABILITY and settings.SENTRY_DSN):
        return
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN,
                        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE)
    except Exception:
        # never block startup on telemetry
        pass


