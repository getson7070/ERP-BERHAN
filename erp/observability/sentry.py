import os
def init_sentry(app):
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.1)
        app.logger.info("Sentry initialized")
    except Exception as e:
        app.logger.warning("Sentry init failed: %s", e)


