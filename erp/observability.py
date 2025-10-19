﻿
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

# --- Phase1: metrics endpoint (Prometheus) ---
def register_metrics_endpoint(app):
    try:
        from flask import Response
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

        @app.get("/metrics")
        def metrics():
            data = generate_latest()  # uses default registry
            return Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception:
        # Keep app booting even if prometheus_client isn't present in some envs
        pass
# --- /Phase1 metrics endpoint ---

# --- Phase1: audit chain flag + gauge ---
try:
    from prometheus_client import Gauge
except Exception:
    class Gauge:  # no-op stub if prometheus_client is missing
        def __init__(self, *a, **k): pass
        def set(self, *a, **k): pass

# Module-level boolean exported via erp.__init__
AUDIT_CHAIN_BROKEN = False

# Prometheus gauge so tests can scrape /metrics
try:
    _AUDIT_CHAIN_BROKEN_G = Gauge(
        "audit_chain_broken", "Audit logging chain broken (1=yes, 0=no)"
    )
    _AUDIT_CHAIN_BROKEN_G.set(0)
except Exception:
    _AUDIT_CHAIN_BROKEN_G = None

def set_audit_chain_broken(flag: bool = True):
    """Mark audit chain as broken/healthy and reflect in metrics."""
    global AUDIT_CHAIN_BROKEN
    AUDIT_CHAIN_BROKEN = bool(flag)
    if _AUDIT_CHAIN_BROKEN_G is not None:
        try:
            _AUDIT_CHAIN_BROKEN_G.set(1 if flag else 0)
        except Exception:
            # Never break the app due to metrics library quirks
            pass
# --- /Phase1 audit chain flag + gauge ---

