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

## UI/UX

All templates leverage Bootstrap 5 for responsive design and mobile parity. `Flask-Babel` powers multi-language support; set `BABEL_DEFAULT_LOCALE` and `BABEL_SUPPORTED_LOCALES` to expose additional translations. A global search bar in the navbar queries CRM, inventory, HR, and finance records. A dark-mode toggle with accessible contrast ratios is persisted in `localStorage`. A service worker (`static/js/sw.js`) ensures offline access and queues actions for sync when the connection restores. The `/dashboard` route delivers role-based views for employees, clients, and admins.

## Blueprints & Templates

Blueprint modules exposing a module-level `bp` are auto-registered from `erp/` and `plugins/`.
See [docs/blueprints.md](docs/blueprints.md) for details. All HTML pages extend `templates/base.html` and share a navbar partial; see [docs/templates.md](docs/templates.md).


## Integration & Ecosystem

- `GET /api/ping` and `POST /api/graphql` expose REST and GraphQL access.
- Webhooks forward events to the configured `WEBHOOK_URL`.
- Plugins in the `plugins/` directory auto-register and are listed at `/plugins`.
- Connectors under `erp/connectors` push invoices or fetch products.
- `sdk.client.ERPClient` provides a lightweight Python SDK.

## Backups

The `backup.py` helper creates timestamped database backups. PostgreSQL and
MySQL connections are dumped via `pg_dump` and `mysqldump`, allowing the dumps
to be used for replication or off-site disaster recovery. See
`docs/db_maintenance.md` for detailed backup/restore and pooling guidance.

## Disaster Recovery

Weekly restore drills validate a **15‑minute RPO** and **one‑hour RTO**. The
process is documented in [docs/dr_plan.md](docs/dr_plan.md) and executed via
`scripts/restore_latest_backup.py`, which restores the most recent dump to a
staging database and records the elapsed time for each run.

## Data Governance

Table‑level retention windows and column lineage are defined in
[docs/data_retention.md](docs/data_retention.md). The `DataLineage` model tracks
the origin of analytics fields, and exports mask PII to meet Ethiopian privacy
requirements.

### Multi-Factor Authentication

Both employee and client accounts are protected with TOTP based multi-factor
authentication. During registration an MFA secret is generated and must be
configured in an authenticator application. Logins require the 6-digit code in
addition to the password.

### Role-Based Access

User roles and permissions are loaded into the session at authentication. The
`roles_required` decorator can be used on management-only routes to enforce role
checks, while `has_permission()` centralizes permission validation and
automatically grants access to users with the *Management* role.

Row level security is enabled on core tables. Each request sets a
`my.org_id` session variable, ensuring queries are transparently filtered to the
tenant’s organization.

### Token-Based Authentication

The `/auth/token` and `/auth/refresh` endpoints issue short-lived access tokens
and rotating refresh tokens. Refresh tokens are stored in Redis with their
`org_id` and user mapping so compromised tokens can be revoked. Tokens include a
`kid` header tied to the `JWT_SECRET_ID` environment variable, enabling seamless
secret rotation. These authentication endpoints are protected by strict per-route
rate limits to mitigate brute-force attempts, with rejections surfaced through
the `rate_limit_rejections_total` Prometheus counter. A k6 smoke script
(`scripts/k6_rate_limit.js`) can be run to stress authentication and verify 429
responses under load.

### Materialized Views

Key performance indicators are pre-aggregated in the `kpi_sales` materialized
view. A Celery beat job periodically executes `REFRESH MATERIALIZED VIEW
CONCURRENTLY kpi_sales` and pushes updates to connected dashboards over
WebSockets for near real-time visibility with short-lived per-tenant tokens.

## Automation & Analytics

Background jobs expand automation and insight capabilities:

- `send_approval_reminders` notifies sales representatives of pending orders.
- `forecast_sales` computes a naive monthly projection of sales trends.
- `generate_compliance_report` writes weekly CSV reports of orders missing status.
- `/analytics/reports` offers a simple report builder for orders and tenders.

## Tender Lifecycle

Tenders progress through defined workflow states culminating in automatic
transitions to **Evaluated** and **Awarded**. When a tender is evaluated the
status becomes *Evaluated*; recording a winning supplier and date moves it to
*Awarded* and stores the `awarded_to` and `award_date` fields.

## Deployment

A production-ready WSGI entrypoint (`wsgi.py`), `Dockerfile`, and `.env.example`
are provided for running the application in a Gunicorn-backed container. Configure
environment variables as needed and build the container with Docker for
consistent deployments. Kubernetes manifests in `deploy/k8s/` illustrate a
high‑availability setup with readiness probes and horizontal pod autoscaling.

## Observability & Offline Use

Requests are instrumented with Prometheus metrics and exposed at `/metrics` for
collection by a monitoring system. Structured logs are emitted to standard
output to aid in tracing and alerting.
Key metrics include `graphql_rejects_total` for GraphQL depth/complexity
violations and `audit_chain_broken_total` for tamper‑evident audit log checks.
Database efficiency is monitored through `db_query_count` tests that guard against
N+1 patterns. Cache performance is tracked with `cache_hits_total`,
`cache_misses_total`, and the `cache_hit_ratio` gauge.

The UI registers a service worker (`static/js/sw.js`) to cache core assets and
API responses. User actions are queued in IndexedDB when offline and replayed to
the API once connectivity returns, providing a more resilient mobile experience.

## Security & Load Testing

Run `scripts/security_scan.sh` for static analysis and dependency checks.
Use `scripts/load_test.sh` or a preferred tool to validate performance at target
concurrency levels.

## Performance Benchmarking

Run `python scripts/benchmark.py` against a target URL to measure request
throughput and validate connection pool tuning or scaling changes.

## Current Audit Priorities
- Recent audits highlighted several cross-cutting gaps. The project is
actively addressing the following items:

- Enforce reverse-proxy rate limiting and publish 429 metrics.
- Expand the CI pipeline so every push or pull request runs linting,
  type checks, tests, dependency and container scans.
- Document recovery objectives and perform regular restore drills to
  validate backups.
- Maintain data retention rules and column-level lineage for analytical
  exports.
- Monitor cache hit rate and query counts to flag inefficient
  database access.
- Automate JWT secret rotation using `JWT_SECRET_ID` and audit each
  rollover.

## Governance & Roadmap

- Refer to `docs/versioning.md` for release numbering and branching conventions.
- Quarterly access recertification steps are outlined in `docs/access_recerts.md`.
- Detailed migration procedures live in `docs/migration_guide.md`.
- User assistance is covered in `docs/in_app_help.md` and `docs/training_tutorials.md`.
- Planned milestones are tracked in `docs/roadmap.md`.
- An in-app `/help` page links to documentation and discussion forums.
- Control mappings to ISO-27001 and Ethiopian data law reside in `docs/control_matrix.md`.
- Quarterly access reviews produce WORM exports via `scripts/access_recert_export.py`.
- Release notes are tracked in `CHANGELOG.md` with rollback steps in `docs/rollback.md`.
