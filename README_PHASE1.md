# ERP-BERHAN — Phase 1 Upgrade Pack

This bundle is additive and safe to merge into your repository. It delivers:
- `/healthz` and `/readyz` endpoints (deterministic boot + probes)
- Environment validation on startup (fail-fast for missing secrets)
- Security defaults (cookie flags, safe headers hook)
- Sentry bootstrap (no-op unless `SENTRY_DSN` is set)
- CI checks for single-head Alembic migrations (prevents drift)
- Tests for health endpoints and readiness checks
- GitHub Actions workflow with ephemeral Postgres + Redis services

> ✅ **No breaking changes**: files are additive under `erp/`, `tools/`, `tests/`, `.github/`, and `deploy/snippets/`.
> After merge, point your app factory to call `apply_security_defaults(app)`, `validate_required_env()`, and register the `health` blueprint.

## How to integrate quickly

1. **Register health blueprint** in your app factory (or `wsgi.py` after the Flask app is created):

```python
try:
    from erp.blueprints.health import bp as health_bp
    app.register_blueprint(health_bp)
except Exception as e:
    app.logger.warning("Health blueprint not registered: %s", e)
```

2. **Fail-fast on missing envs** early during boot (before serving requests):

```python
from erp.config.validate_env import validate_required_env, REQUIRED_ENV_DEFAULT
validate_required_env(REQUIRED_ENV_DEFAULT)
```

3. **Apply security defaults** (cookies & headers) once at init time:

```python
from erp.config.security import apply_security_defaults, register_secure_headers
apply_security_defaults(app)
register_secure_headers(app)
```

4. **(Optional) Sentry** — enable if `SENTRY_DSN` is set:

```python
from erp.observability.sentry import init_sentry
init_sentry(app)
```

5. **CI** — commit this bundle and push. The workflow in `.github/workflows/ci-phase1.yml` will:
   - Start Postgres + Redis
   - Run tests
   - Gate on single-head Alembic (if `alembic.ini` exists)

6. **Render Health Checks** — copy `deploy/snippets/render.healthchecks.yaml` into your existing `render.yaml`
   service and set `healthCheckPath: /healthz`. If you have a readiness probe, map it to `/readyz` via webhooks or startup script.

## Environment variables

Copy `.env.example` to your environment (Render, App Runner, Docker) and fill real values:

- `SECRET_KEY` — Flask secret key
- `DATABASE_URL` — e.g., `postgresql+psycopg2://user:pass@host:5432/dbname`
- `REDIS_URL` — e.g., `redis://host:6379/0`
- `SENTRY_DSN` — *(optional)*
- `DEPLOY_HOOK_URL` — *(optional; read from env, never commit secrets)*

## Notes on Alembic

The CI job `tools/ci/check_alembic_single_head.sh` enforces a **single** Alembic head.
- If you currently have multiple heads, squash them into a single head **before** enabling enforce mode in CI.
- The script detects `alembic.ini`. If absent, the check is skipped.

## Quick test locally

```bash
pip install -r requirements.txt || true
pip install -r requirements-phase1.txt
pytest -q
```

## Support

If `/readyz` returns 503 in dev/CI, check that Postgres and Redis are reachable via `DATABASE_URL` and `REDIS_URL`.
