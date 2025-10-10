"""
observability_ext.py: Observability integrations for BERHAN ERP.

This module initializes observability tools like Sentry and metrics counters.
"""

import os

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except ImportError:
    sentry_sdk = None  # Sentry is optional

try:
    # Prometheus client is optional
    from prometheus_client import Counter
except ImportError:
    Counter = None

# Define counters (will be None if prometheus_client is not installed)
TOKEN_ERRORS = Counter("token_errors", "Total MFA token errors") if Counter else None
GRAPHQL_REJECTS = Counter("graphql_rejects", "Total GraphQL rejects") if Counter else None

def init_observability(app):
    """
    Initialize observability services like Sentry and metrics.

    Args:
        app: Flask application instance
    """
    # Setup Sentry if a DSN is configured
    dsn = os.getenv("SENTRY_DSN") or app.config.get("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT") or app.config.get("ENVIRONMENT")
    if dsn and sentry_sdk:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.2,
            environment=environment or "production",
        )

    # Potentially register other observability tools here
    return
