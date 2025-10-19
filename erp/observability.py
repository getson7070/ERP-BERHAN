
from __future__ import annotations
import logging, os, sys, json, time, uuid
from flask import g, request

def _json_formatter(record: logging.LogRecord) -> str:
    payload = {
        "ts": int(time.time() * 1000),
        "level": record.levelname,
        "msg": record.getMessage(),
        "logger": record.name,
        "request_id": getattr(g, "request_id", None),
        "path": getattr(request, "path", None),
        "method": getattr(request, "method", None),
    }
    return json.dumps(payload, ensure_ascii=False)

class JsonStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        try:
            msg = _json_formatter(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            logging.StreamHandler.emit(self, record)

def init_logging(app, level: str | None = None):
    level_name = level or os.getenv("LOG_LEVEL", "INFO")
    lvl = getattr(logging, level_name.upper(), logging.INFO)
    handler = JsonStreamHandler(stream=sys.stdout)
    handler.setLevel(lvl)
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(lvl)

    @app.before_request
    def _rid_before():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    @app.after_request
    def _rid_after(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers.setdefault("X-Request-ID", rid)
        return resp

    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        try:
            import sentry_sdk  # type: ignore
            from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore
            sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()])
            app.logger.info("sentry_initialized")
        except Exception as e:  # pragma: no cover
            app.logger.warning(f"sentry_init_failed: {e}")
    return app
