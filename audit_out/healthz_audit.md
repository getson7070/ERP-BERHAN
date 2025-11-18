# Health endpoint audit (limited)

## Scope
- Verified health check routing used by `/healthz` endpoint within Flask application factory.
- Executed focused pytest covering `tests/routes/test_healthz.py` to validate expected degradation response when dependencies are unavailable.

## Findings
- `/healthz` fallback route in `erp/__init__.py` bypassed blueprint in `erp.routes.health`, returning HTTP 200 even when backend services failed. This broke failure reporting logic and associated test.

## Actions taken
- Registered `erp.routes.health` blueprint in `_DEFAULT_BLUEPRINT_MODULES` to ensure health endpoints use dependency checks rather than the static fallback.
- Re-ran `pytest tests/routes/test_healthz.py` to confirm correct 503 response when database and Redis checks fail.

## Next steps
- Consider consolidating other health-related blueprints (`erp.health_checks`, `erp.blueprints.health_compat`, `erp.ops.health`) to reduce duplication.
- Add integration tests that simulate real database/Redis outages if infrastructure is available, ensuring accurate SLO tracking for uptime monitors.
- Enable Flask-Limiter and Flask-Mail in deployments where applicable to restore full observability and alerting.
