# BERHAN PHARMA

[![CI](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)

BERHAN PHARMA: A Flask-based ERP for pharmaceutical management, including inventory, analytics, and compliance.

## Setup

```bash
git clone https://github.com/getson7070/ERP-BERHAN.git
cd ERP-BERHAN
pip install -r requirements.txt
flask run
```

## Tech Stack

- Flask
- PostgreSQL
- SQLAlchemy
- Celery
- Redis
- PgBouncer
- Bootstrap 5

## CI Pipeline

Every push and pull request runs ruff, flake8, mypy, pytest with coverage,
Bandit, pip-audit, gitleaks, Docker build with Trivy, kube-linter, kube-score,
OWASP ZAP baseline, and pa11y accessibility checks. Branch protection requires
all checks to pass before merging.

Developer-facing lint and type rules are centralised in `.flake8` and `mypy.ini`.
Run `flake8` and `mypy erp` locally to catch issues before pushing.

### Pre-commit hooks

Install and enable the pre-commit hooks to mirror CI checks:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

Running `pre-commit run --files <files>` will execute ruff, black, and mypy on the staged changes.

## Project Status
An initial audit of the repository rated the project **2/10** overall,
highlighting that many features remain as plans. The detailed findings and
improvement plan are captured in [docs/audit_summary.md](docs/audit_summary.md).

## Environment Variables

The application pulls configuration from environment variables. Key settings include:

- `FLASK_SECRET_KEY` – secret key for session and CSRF protection.
 - `DATABASE_URL` – PostgreSQL connection string used by SQLAlchemy.
 - `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`/`DB_POOL_TIMEOUT` – connection pool tuning
   knobs for high‑load deployments.
- `ADMIN_USERNAME`/`ADMIN_PASSWORD` – credentials used for initial admin seeding.
- `MFA_ISSUER` – issuer name shown in authenticator apps for MFA codes.
- `JWT_SECRETS`/`JWT_SECRET_ID` – map of versioned JWT secrets with active `kid` for rotation.
- `RATE_LIMIT_DEFAULT` – global rate limit (e.g. `100 per minute`).
- `LOCK_THRESHOLD`/`ACCOUNT_LOCK_SECONDS` – progressive backoff and
  temporary account lock settings.
- `GRAPHQL_MAX_DEPTH` – maximum allowed GraphQL query depth.
- `GRAPHQL_MAX_COMPLEXITY` – maximum allowed GraphQL query complexity.
- `VAULT_FILE` – optional JSON file providing secrets for automated rotation.
- `OAUTH_CLIENT_ID`/`OAUTH_CLIENT_SECRET` – credentials for SSO/OAuth2 login.
- `OAUTH_AUTH_URL`/`OAUTH_TOKEN_URL`/`OAUTH_USERINFO_URL` – endpoints for the OAuth2 provider.
- `ARGON2_TIME_COST`, `ARGON2_MEMORY_COST`, `ARGON2_PARALLELISM` – password hashing parameters.
- `BABEL_DEFAULT_LOCALE`/`BABEL_SUPPORTED_LOCALES` – default and available locales for UI translations.
- `API_TOKEN` – bearer token used to authorize REST and GraphQL requests.
- `ACCOUNTING_URL` – base URL for the accounting connector.
- `S3_RETENTION_DAYS` – optional lifecycle policy for object storage.
- `USE_FAKE_REDIS` – set to `1` during testing to use an in-memory Redis emulator.

The analytics module uses Celery for scheduled reporting. Configure the broker
and result backend via the following environment variables:

- `CELERY_BROKER_URL` – URL of the message broker (default
  `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` – URL of the result backend (default
  `redis://localhost:6379/0`)

Set these variables in your deployment environment to point Celery to your
Redis instance. During local testing you may set `USE_FAKE_REDIS=1` to avoid
running a dedicated Redis server.

## Automation & Analytics

Celery powers several background workflows:

- Scheduled tasks send pending order reminders and generate monthly compliance
  reports.
- KPI materialized views refresh every five minutes and a simple forecast of next
  month's sales is displayed on the analytics dashboard. A nightly export pushes
  KPIs to a Timescale/ClickHouse warehouse, incrementing the
  `olap_export_success_total` counter, and staleness is tracked via the
  `kpi_sales_mv_age_seconds` metric.
- Visit `/analytics/report-builder` to generate ad-hoc order or maintenance
  reports and schedule compliance exports.
- Monitor Celery backlog with `python scripts/monitor_queue.py` to detect stuck tasks.

## Caching

List pages in CRM and inventory cache results in Redis to reduce database load.
Mutating routes invalidate the relevant `<module>:<org_id>` key to keep data
consistent. See `docs/cache_invalidation.md` for details.

## Database Migrations

Schema changes are managed with Alembic. Apply migrations with:

```
alembic upgrade head
```

Run this command after pulling updates to keep your database schema in sync.

### Local PostgreSQL Setup

Unit tests and the development server expect a running PostgreSQL instance.
If the service is missing you may see errors like
`psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused`.

Provision a local server by executing:

```
scripts/setup_postgres.sh
```

The helper installs PostgreSQL (if necessary), starts the default cluster,
configures the default `postgres` user with password `postgres`, creates the
`erp` database if missing, and performs a `pg_isready` connectivity check so
failures surface before running tests.

If connectivity issues persist, see
`docs/postgres_troubleshooting.md` for additional diagnostics.

## Security

Session cookies are configured with `Secure`, `HttpOnly` and `SameSite=Lax`.
[`Flask-Talisman`](https://github.com/GoogleCloudPlatform/flask-talisman) enforces HTTPS
and sets modern security headers; ensure the app is served over TLS.

SSO/OAuth2 login is available via the configured provider. Successful and failed
authentication attempts are recorded in an `audit_logs` table protected by
row-level security and hash-chained for tamper evidence.

For encryption at rest, deploy PostgreSQL with disk-level encryption or
transparent data encryption and rotate `JWT_SECRET` and other credentials using a
secrets manager; see [docs/security/secret_rotation.md](docs/security/secret_rotation.md).
