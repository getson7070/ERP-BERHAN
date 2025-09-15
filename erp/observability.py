"""Observability helpers and OpenTelemetry wiring."""

from __future__ import annotations

import importlib.util
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from prometheus_client import Counter, Gauge, Histogram

from db import redis_client

APDEX_THRESHOLD = float(os.environ.get("APDEX_T", "0.5"))

REQUEST_COUNT = Counter(
    "request_count",
    "HTTP Request Count",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency", ["endpoint"])
TOKEN_ERRORS = Counter("token_errors_total", "Invalid or expired token events")
QUEUE_LAG = Gauge("queue_lag", "Celery queue backlog size", ["queue"])
KPI_SALES_MV_AGE = Gauge(
    "kpi_sales_mv_age_seconds",
    "Age of the kpi_sales materialized view in seconds",
)
RATE_LIMIT_REJECTIONS = Counter(
    "rate_limit_rejections_total", "Requests rejected due to rate limiting"
)
GRAPHQL_REJECTS = Counter(
    "graphql_rejects_total",
    "GraphQL queries rejected for depth or complexity limits",
)
AUDIT_CHAIN_BROKEN = Counter(
    "audit_chain_broken_total",
    "Detected breaks in the audit log hash chain",
)
OLAP_EXPORT_SUCCESS = Counter(
    "olap_export_success_total",
    "Number of successful OLAP exports",
)
APDEX_SATISFIED = Counter(
    "apdex_satisfied_total", "Requests with latency <= threshold/2"
)
APDEX_TOLERATING = Counter(
    "apdex_tolerating_total", "Requests with latency <= threshold"
)
APDEX_FRUSTRATED = Counter(
    "apdex_frustrated_total", "Requests with latency > threshold"
)
APDEX_SCORE = Gauge("apdex_score", "Current Apdex score")
APDEX_SCORE.set(1.0)


@dataclass
class SLOCard:
    slug: str
    title: str
    target: str
    current: str
    status: str
    status_label: str
    badge_class: str
    description: str
    detail: str | None = None
    error_budget_remaining: str | None = None
    progress: float | None = None
    footnote: str | None = None


def _format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0m"
    total_seconds = int(seconds)
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs and not parts:
        parts.append(f"{secs}s")
    return " ".join(parts[:3])


def _sum_counter(
    counter: Counter, predicate: Callable[[dict[str, str]], bool] | None = None
) -> float:
    total = 0.0
    for metric in counter.collect():
        for sample in metric.samples:
            if not sample.name.endswith("_total"):
                continue
            labels = sample.labels or {}
            if predicate is None or predicate(labels):
                total += sample.value
    return float(total)


def _status_from_budget(
    consumed_fraction: float, meets_objective: bool
) -> tuple[str, str, str]:
    if not meets_objective or consumed_fraction >= 1:
        return "breach", "Breach", "danger"
    if consumed_fraction >= 0.5:
        return "watch", "At Risk", "warning"
    return "healthy", "Healthy", "success"


def _status_from_threshold(
    value: float, target: float, warn_delta: float, higher_is_better: bool = True
) -> tuple[str, str, str]:
    comparison_value = value - target if higher_is_better else target - value
    if (higher_is_better and value < target) or (
        not higher_is_better and value > target
    ):
        return "breach", "Breach", "danger"
    if comparison_value <= warn_delta:
        return "watch", "At Risk", "warning"
    return "healthy", "Healthy", "success"


def _status_from_bounds(
    value: float, warning: float, breach: float
) -> tuple[str, str, str]:
    if value >= breach:
        return "breach", "Breach", "danger"
    if value >= warning:
        return "watch", "At Risk", "warning"
    return "healthy", "Healthy", "success"


def _collect_queue_backlog() -> float:
    try:
        backlog = float(redis_client.llen("celery"))
    except Exception:
        backlog = QUEUE_LAG.labels("celery")._value.get()
    else:
        QUEUE_LAG.labels("celery").set(backlog)
    return backlog


def build_slo_dashboard(config: dict[str, Any]) -> dict[str, Any]:
    from flask import current_app

    from erp.routes import analytics

    total_requests = _sum_counter(REQUEST_COUNT)
    server_errors = _sum_counter(
        REQUEST_COUNT, lambda labels: labels.get("http_status", "").startswith("5")
    )
    availability = 100.0
    error_rate = 0.0
    if total_requests:
        error_rate = server_errors / total_requests
        availability = (1 - error_rate) * 100

    availability_target = float(config.get("SLO_AVAILABILITY_TARGET", 99.9))
    window_days = int(config.get("SLO_AVAILABILITY_WINDOW_DAYS", 30))
    window_seconds = window_days * 86_400
    budget_fraction = max(0.0, 1 - availability_target / 100.0)
    budget_seconds = budget_fraction * window_seconds
    consumed_fraction = 0.0
    if budget_fraction > 0:
        consumed_fraction = min(1.0, error_rate / budget_fraction)
    remaining_seconds = max(0.0, (1 - consumed_fraction) * budget_seconds)
    availability_status, availability_label, availability_badge = _status_from_budget(
        consumed_fraction, availability >= availability_target
    )

    availability_card = SLOCard(
        slug="availability",
        title="API availability",
        target=f">= {availability_target:.1f}%",
        current=f"{availability:.3f}%",
        status=availability_status,
        status_label=availability_label,
        badge_class=availability_badge,
        description="Rolling 30-day objective for successful responses",
        detail=f"{error_rate * 100:.3f}% error rate across {int(total_requests)} requests",
        error_budget_remaining=_format_duration(remaining_seconds),
        progress=round(consumed_fraction * 100, 1),
        footnote="Error budget assumes equal load distribution across the window.",
    )

    apdex_target = float(config.get("SLO_APDEX_TARGET", 0.85))
    apdex_value = APDEX_SCORE._value.get()
    apdex_status, apdex_label, apdex_badge = _status_from_threshold(
        apdex_value, apdex_target, warn_delta=0.05
    )
    apdex_card = SLOCard(
        slug="apdex",
        title="Apdex score",
        target=f">= {apdex_target:.2f}",
        current=f"{apdex_value:.3f}",
        status=apdex_status,
        status_label=apdex_label,
        badge_class=apdex_badge,
        description="User satisfaction derived from the Apdex formula",
        detail=f"Latency threshold (T) = {APDEX_THRESHOLD * 1000:.0f}ms",
    )

    backlog_target = float(config.get("SLO_QUEUE_BACKLOG_TARGET", 50))
    backlog_warning = float(config.get("SLO_QUEUE_BACKLOG_WARNING", 75))
    backlog_breach = float(config.get("SLO_QUEUE_BACKLOG_BREACH", 100))
    backlog_value = _collect_queue_backlog()
    backlog_status, backlog_label, backlog_badge = _status_from_bounds(
        backlog_value, backlog_warning, backlog_breach
    )
    backlog_card = SLOCard(
        slug="queue",
        title="Queue backlog",
        target=f"<= {backlog_target:.0f} jobs",
        current=f"{backlog_value:.0f} jobs",
        status=backlog_status,
        status_label=backlog_label,
        badge_class=backlog_badge,
        description="Celery queue depth averaged over the last scrape",
        detail="Auto-scalers trigger if sustained backlog exceeds warning thresholds.",
    )

    freshness_target = float(config.get("SLO_MV_FRESHNESS_TARGET", 900))
    freshness_warning = float(config.get("SLO_MV_FRESHNESS_WARNING", 1200))
    freshness_breach = float(config.get("SLO_MV_FRESHNESS_BREACH", 1800))
    mv_age = analytics.kpi_staleness_seconds()
    freshness_status, freshness_label, freshness_badge = _status_from_bounds(
        mv_age, freshness_warning, freshness_breach
    )
    freshness_card = SLOCard(
        slug="freshness",
        title="Sales MV freshness",
        target=f"<= {freshness_target / 60:.0f} minutes",
        current=_format_duration(mv_age),
        status=freshness_status,
        status_label=freshness_label,
        badge_class=freshness_badge,
        description="Age of the sales materialized view (kpi_sales)",
        detail="Refresh automation runs every 10 minutes with back-pressure guards.",
    )

    cards: list[SLOCard] = [availability_card, apdex_card, backlog_card, freshness_card]
    severity_order = {"healthy": 0, "watch": 1, "breach": 2}
    overall_status = max(cards, key=lambda c: severity_order[c.status]).status
    overall_label = max(cards, key=lambda c: severity_order[c.status]).status_label
    overall_badge = max(cards, key=lambda c: severity_order[c.status]).badge_class

    snapshot = {
        "generated_at": datetime.now(UTC),
        "cards": cards,
        "overall_status": overall_status,
        "overall_label": overall_label,
        "overall_badge": overall_badge,
        "availability_error_budget_consumed": availability_card.progress,
    }
    current_app.logger.debug(
        "slo_snapshot",  # structured log for trace correlation
        extra={
            "availability": availability,
            "availability_target": availability_target,
            "apdex": apdex_value,
            "queue_backlog": backlog_value,
            "mv_age_seconds": mv_age,
        },
    )
    return snapshot


_OTEL_INITIALISED = False


def _parse_headers(raw: str | None) -> dict[str, str] | None:
    if not raw:
        return None
    headers: dict[str, str] = {}
    for part in raw.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


def configure_opentelemetry(app, db) -> None:
    global _OTEL_INITIALISED
    endpoint = app.config.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    enabled = bool(app.config.get("OTEL_ENABLED")) or bool(endpoint)
    if _OTEL_INITIALISED or not enabled:
        return

    from opentelemetry import metrics as otel_metrics
    from opentelemetry import trace
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    log_exporter_spec = importlib.util.find_spec(
        "opentelemetry.exporter.otlp.proto.http.log_exporter"
    )
    if log_exporter_spec is not None:
        from opentelemetry.exporter.otlp.proto.http.log_exporter import OTLPLogExporter
    else:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

    endpoint = endpoint or "http://localhost:4318"
    timeout = float(app.config.get("OTEL_EXPORT_TIMEOUT", 10.0))
    interval = float(app.config.get("OTEL_METRIC_EXPORT_INTERVAL", 15.0))
    headers = _parse_headers(app.config.get("OTEL_EXPORTER_OTLP_HEADERS"))
    resource = Resource.create(
        {
            SERVICE_NAME: app.config.get("OTEL_SERVICE_NAME", "erp-berhan"),
            "service.instance.id": app.config.get(
                "OTEL_SERVICE_INSTANCE_ID",
                os.environ.get("HOSTNAME", str(uuid.uuid4())),
            ),
            "deployment.environment": os.environ.get("APP_ENV", "production"),
            SERVICE_VERSION: app.config.get(
                "RELEASE_VERSION",
                os.environ.get("RELEASE_VERSION", "dev"),
            ),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(
        endpoint=endpoint, headers=headers, timeout=timeout
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metric_exporter = OTLPMetricExporter(
        endpoint=endpoint, headers=headers, timeout=timeout
    )
    reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=int(interval * 1000),
        export_timeout_millis=int(timeout * 1000),
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    otel_metrics.set_meter_provider(meter_provider)

    log_exporter = OTLPLogExporter(endpoint=endpoint, headers=headers, timeout=timeout)
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    def _request_hook(span, environ):
        if span is None:
            return
        corr = environ.get("HTTP_X_CORRELATION_ID")
        if corr:
            span.set_attribute("http.request_id", corr)

    FlaskInstrumentor().instrument_app(app, request_hook=_request_hook)
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)
    with app.app_context():
        SQLAlchemyInstrumentor().instrument(engine=db.engine)

    _OTEL_INITIALISED = True
