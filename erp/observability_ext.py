"""Observability integrations for ERP-BERHAN.

This module initializes Sentry for error tracking and exposes simple counters.
"""

import os

try:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore
except ImportError:
    sentry_sdk = None  # type: ignore
    FlaskIntegration = None  # type: ignore

# Example counters/lists used elsewhere.
TOKEN_ERRORS: list[str] = []
GRAPHQL_REJECTS: list[str] = []


def init_observability(app) -> None:
    """Initialize observability providers for the given Flask app.

    This currently integrates Sentry for error tracking if a DSN is configured.
    It looks for SENTRY_DSN in environment variables or in app.config.
    Optionally reads SENTRY_TRACES_SAMPLE_RATE for performance tracing.
    """
    if sentry_sdk is None or FlaskIntegration is None:
        return

    dsn = os.getenv("SENTRY_DSN") or app.config.get("SENTRY_DSN")
    if not dsn:
        return

    trace_rate_str = os.getenv("SENTRY_TRACES_SAMPLE_RATE") or str(app.config.get("SENTRY_TRACES_SAMPLE_RATE", 0.1))
    try:
        trace_rate = float(trace_rate_str)
    except (TypeError, ValueError):
        trace_rate = 0.1

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=trace_rate,
        send_default_pii=True,
    )
