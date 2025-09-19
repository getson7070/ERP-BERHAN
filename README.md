# BERHAN PHARMA

[![Build](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=build)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![Coverage](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=coverage)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![ZAP](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=ZAP)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![Trivy](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=Trivy)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![Pa11y](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=Pa11y)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![SBOM](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml/badge.svg?label=SBOM)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml)
[![SLSA](https://github.com/getson7070/ERP-BERHAN/actions/workflows/generator-generic-ossf-slsa3-publish.yml/badge.svg?label=SLSA)](https://github.com/getson7070/ERP-BERHAN/actions/workflows/generator-generic-ossf-slsa3-publish.yml?query=branch%3Amain)

BERHAN PHARMA: A Flask-based ERP for pharmaceutical management, including inventory, analytics, compliance, and traceability.
This release adds electronic signatures, GMP batch record tracking, native lot/serial management with recall simulation, and predictive analytics for demand forecasting. Core security features include universal CSRF protection, rate limiting and a lightweight WAF that blocks obvious injection attempts. OAuth2 login uses PKCE, passkeys are supported via WebAuthn, and JWTs support key rotation with Redis-backed revocation.

Signed webhooks and OAuth-friendly connectors expose a secure integration surface for services like Power BI and external manufacturing systems. A dedicated integration API exposes REST and GraphQL endpoints for connecting external systems.

An OpenAPI 3.1 specification (`docs/OPENAPI.yaml`) documents all REST and webhook interfaces, and incoming analytics payloads are validated against JSON Schemas. WebSocket clients must present a JWT token during the connection handshake.

The UI is optimized for mobile devices and supports offline use via a Progressive Web App manifest and service worker.
Offline caching is verified in CI with a Playwright test to ensure core routes remain available without network connectivity.

Core Web Vitals are monitored in-browser via the `web-vitals` library, and server-side Apdex scores track latency against a 0.5 s target. Static assets ship with ETags and long-lived cache headers to accelerate repeat visits.
An accessible locale switcher enables English, Amharic, and Farsi translations, and a lightweight guided tour introduces key UI controls for new users.
ARIA landmarks and `aria-current` hints target WCAG 2.1 AA compliance across templates.
Policies and procedures follow the BERHAN Pharma SOP and corporate policy (see docs/BERHAN_SOP_PACK.md).
A high-level mapping of ERP features to corporate policy pillars is documented in [docs/CORPORATE_POLICY_ALIGNMENT.md](docs/CORPORATE_POLICY_ALIGNMENT.md).

Structured JSON logs capture correlation IDs without blocking database writes.

Third-party scripts are served from CDNs with Subresource Integrity (SRI) hashes and can be mirrored locally for offline deployments.
`/health` (aliased as `/healthz`) exposes a lightweight database and Redis check for container probes.
Deployment configuration is centralized in `apprunner.yaml`; the Dockerfile mirrors its runtime command.
SQL operations use parameterized queries for database portability, and the service worker securely reattaches auth tokens when replaying queued requests.
Row-level security policies derive the tenant ID from `current_setting('erp.org_id')` to enforce per-organization isolation.
Nightly backups (`scripts/pg_backup.sh`), a `scripts/check_indexes.py` CI guard,
and the `scripts/index_audit.py` report provide disaster recovery coverage and
highlight queries that require indexes.
Database maintenance practices, including RPO/RTO targets and indexing benchmarks, are documented in `DATABASE.md`.

## Release & SLOs

Service level objectives target p95 latency and error rates within documented budgets. Releases follow a weekly PATCH, monthly MINOR, and quarterly MAJOR cadence gated on green CI and canary health.

## Local Development Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env  # update FLASK_SECRET_KEY, JWT_SECRETS, DATABASE_URL
docker compose up -d db redis
scripts/run_migrations.sh && python init_db.py
flask run &
celery -A erp.celery worker &
celery -A erp.celery beat &
pytest tests/smoke/test_homepage.py
```

> **Windows users:** follow the PowerShell walkthrough in [docs/local_dev_quickstart.md](docs/local_dev_quickstart.md) to install Python 3.11 with the launcher, generate strong secrets, and choose between Docker-backed PostgreSQL or the SQLite fallback. Always install dependencies from `requirements.lock` to avoid slow wheel builds on Windows.

This sequence sets up the environment, seeds an admin user, runs the web app and separate Celery worker and beat processes, and finishes with a smoke test.
For a walkthrough with sample data see [docs/guided_setup.md](docs/guided_setup.md).

**Windows tips:** use `py -3.11 -m venv .venv` followed by `.\.venv\Scripts\Activate.ps1`, and ensure PostgreSQL is running (`docker compose up -d db`) or export `DATABASE_URL`/`ALEMBIC_URL` before executing `scripts/run_migrations.sh`.

## Local tooling

Copy `.env.example` to `.env` and adjust values for your environment. The `.env` file is ignored by git and should never be committed.

Run `scripts/install_tools.sh` to provision auxiliary security and accessibility
utilities (gitleaks, Trivy, kube-linter, kube-score, Pa11y, OWASP ZAP baseline,
Playwright browsers) along with the system libraries they require.

Pa11y needs the Chromium sandbox disabled when executed as root:
`PUPPETEER_ARGS="--no-sandbox" pa11y http://localhost:5000` or run the
preconfigured `scripts/run_pa11y.sh` script for common routes.
Run `zap-baseline.py -t http://localhost:5000` for the OWASP ZAP baseline scan.

| Report | Artifact |
|--------|---------|
| Coverage HTML | [coverage-html](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| Bandit | [bandit-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| pip-audit | [pip-audit-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| Trivy | [trivy-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| SBOM | [sbom](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| ZAP | [zap-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| Pa11y | [pa11y-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| DR Drill (RPO/RTO) | [dr-drill-report](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |
| Access Recert Export | [access-recert-export](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain) |

### Auditor Quick Links
- [Daily audit chain verifier](https://github.com/getson7070/ERP-BERHAN/actions/workflows/audit-chain.yml?query=branch%3Amain)
- [templates/partials/saved_views.html](templates/partials/saved_views.html) & [static/js/saved_views.js](static/js/saved_views.js)
- [JWT secret rotation runbook](docs/security/secret_rotation.md) and [test](tests/test_jwt_rotation.py)
- [app.py](app.py)
- [security.py](security.py) – JWT, Talisman, rate limiting, and GraphQL caps
- [Authentication and identity guide](docs/IDENTITY_GUIDE.md)
- [erp/audit.py](erp/audit.py#L1-L67) and [hash-chain migration](migrations/versions/7b8c9d0e1f2_add_audit_hash_chain.py#L1-L18)
- [static/js/sw.js](static/js/sw.js)
- [deploy/k8s/](deploy/k8s)
- [dockerfile](dockerfile)
- [GraphQL complexity guard](erp/routes/api.py#L140-L150)
- [templates/base.html](templates/base.html)
- [templates/partials/navbar.html](templates/partials/navbar.html)
- [templates/partials/breadcrumbs.html](templates/partials/breadcrumbs.html)
- [Onboarding tour](docs/onboarding_tour.md)
- [Control matrix](docs/control_matrix.md)
- [Access recertification guide](docs/access_recerts.md)
- [Design system tokens](docs/design_system.md)
- [JWT secret rotation runbook](docs/security/secret_rotation.md)
- [Master SOP template and priority procedures](docs/BERHAN_SOP_PACK.md)

Latest operational metrics are published in the [status page](docs/status.md).

## Contributing

All commits to `main` must be GPG-signed (`git commit -S`) and receive
approval from a designated CODEOWNER. See [codeowners](codeowners)
for reviewer assignments.

## Setup

See [docs/local_dev_quickstart.md](docs/local_dev_quickstart.md) for a condensed walkthrough.

```bash
git clone https://github.com/getson7070/ERP-BERHAN.git
cd ERP-BERHAN
pip install -r requirements.lock
# Install security tooling and browsers
bash scripts/install_tools.sh
# Enable template auto-reload during development
export FLASK_DEBUG=1
docker compose up -d db redis
scripts/run_migrations.sh
python init_db.py  # seeds initial admin
flask run
```

`FLASK_DEBUG` controls template auto-reload. Leave it unset in production to
avoid unnecessary file-system checks.
If Docker is unavailable, `scripts/setup_postgres.sh` provisions a local
PostgreSQL service before running migrations. Alternatively export `DATABASE_URL` (and optionally `ALEMBIC_URL`) to reuse an existing database or a SQLite file; the migration helper and Alembic environment will honour the override.
See [docs/guided_setup.md](docs/guided_setup.md) for a walkthrough with sample data and first-run tips.

## Deploying on AWS App Runner

**Source build (uses `apprunner.yaml`):**
- Source directory: `/`
- Health check: HTTP `/health`
- Port: `8080`
 - Build command: `python3 -m pip install --upgrade pip setuptools wheel && python3 -m pip install --no-cache-dir -r requirements.lock`
- Runtime env (from Secrets Manager):
  - `APP_ENV` = `production`
  - `FLASK_SECRET_KEY`
  - `JWT_SECRET`
  - `DATABASE_URL` (e.g. `postgresql://user:pass@rds-endpoint:5432/db?sslmode=require` or `sqlite:////tmp/erp.db`)
  - `REDIS_URL`
  - set `AWS_SECRETS_PREFIX` so the app can resolve secrets from AWS Secrets Manager
  - Start command: `gunicorn --bind 0.0.0.0:${PORT:-8080} wsgi:app` (run `scripts/run_migrations.sh` beforehand)
 
**Container image build:**
1. `docker build -t erp-berhan:latest .`
2. `docker tag erp-berhan:latest ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/erp-berhan:latest`
3. `docker push ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/erp-berhan:latest`
4. Configure App Runner or Elastic Beanstalk to use this ECR image and container port `8080`; health path `/health`.

**Notes:**
  - `DATABASE_URL` must be set; the application will not start without it. Do not use `localhost` in `DATABASE_URL`.
- Set `REDIS_URL=redis://…` (ElastiCache + VPC connector) and avoid `USE_FAKE_REDIS` in production.
- Store secrets such as `FLASK_SECRET_KEY`, `JWT_SECRET`, and database credentials in AWS Secrets Manager and expose them via `AWS_SECRETS_PREFIX`.
- Push the latest `main` branch to GitHub before deploying.

## Tech Stack

- Flask
- PostgreSQL
- SQLAlchemy
- Celery
- Redis
- PgBouncer
- Bootstrap 5

## CI Pipeline

Every push and pull request runs ruff, mypy, pytest with coverage,
Bandit, pip-audit, gitleaks, Docker build with Trivy, kube-linter, kube-score,
OWASP ZAP baseline, and pa11y accessibility checks. Branch protection requires
all checks to pass before merging. Commits must be GPG-signed and changes touching
protected paths require codeowners review. A dedicated workflow verifies commit
signatures on pull requests.
Database migrations are smoke-tested with `scripts/run_migrations.sh`, and a separate
performance workflow runs N+1 and slow-query guards under `tests/perf`. A Selenium smoke
test exercises the homepage to catch gross browser regressions. The CI job also emits a
CycloneDX SBOM and uploads disaster-recovery drill timing artifacts for auditors.

## Performance Targets
- API p95 latency < 500ms
- Background jobs sustain 100 tasks/min with <1 min queue lag
Nightly [soak tests](scripts/soak_test.sh) run via the [performance workflow](https://github.com/getson7070/ERP-BERHAN/actions/workflows/perf.yml?query=branch%3Amain).
Developer-facing lint and type rules are centralised in `.flake8` and `mypy.ini`.
Run `ruff` and `mypy erp` locally to catch issues before pushing.

### Running tests

Install development dependencies and run the linters and test suite to ensure all checks pass:

```bash
pip install -r requirements.lock
ruff check .
pytest
```

### Pre-commit hooks

Install and enable the pre-commit hooks to mirror CI checks:

```bash
pip install -r requirements.lock
pre-commit install
```

Running `pre-commit run --files <files>` will execute ruff, black, and mypy on the staged changes.
## Dependency Updates
Dependencies are pinned for reproducibility. Update checks run monthly and patches are applied during the first week of each month.
## Project Status
An initial audit of the repository rated the project **2/10** overall,
highlighting that many features remain as plans. The detailed findings and
improvement plan are captured in [docs/audit_summary.md](docs/audit_summary.md).

## Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) when interacting with the project.

## Design System

See [docs/style_guide.md](docs/style_guide.md) for component and accessibility guidelines.
Spacing and typography tokens are documented in [docs/design_system.md](docs/design_system.md) to keep layouts consistent.

## Onboarding Tour

A quick start guide for new users lives in [docs/onboarding_tour.md](docs/onboarding_tour.md).

## Environment Variables

The application pulls configuration from environment variables. Key settings include:

- `FLASK_SECRET_KEY` – secret key for session and CSRF protection.
- `DATABASE_URL` – PostgreSQL connection string used by SQLAlchemy (append `?sslmode=require`).
- `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`/`DB_POOL_TIMEOUT` – connection pool tuning
  knobs for high‑load deployments.
- `ADMIN_USERNAME`/`ADMIN_PASSWORD` – credentials used for initial admin seeding (only when `SEED_DEMO_DATA=1`).
- `SEED_DEMO_DATA` – set to `1` to populate demo users; never enable in production.
- `MFA_ISSUER` – issuer name shown in authenticator apps for MFA codes.
- `WEBAUTHN_RP_ID`/`WEBAUTHN_RP_NAME`/`WEBAUTHN_ORIGIN` – WebAuthn relying party identifiers.
- `JWT_REVOCATION_TTL` – seconds to retain revoked JWT identifiers in Redis.
- `JWT_SECRETS`/`JWT_SECRET_ID` – map of versioned JWT secrets with active `kid` for rotation.
- `SENTRY_DSN` – capture unhandled errors to Sentry.
- `RATE_LIMIT_DEFAULT` – global rate limit (e.g. `100 per minute`).
- `LOCK_THRESHOLD`/`ACCOUNT_LOCK_SECONDS` – progressive backoff and
  temporary account lock settings.
- `GRAPHQL_MAX_DEPTH` – maximum allowed GraphQL query depth.
- `GRAPHQL_MAX_COMPLEXITY` – maximum allowed GraphQL query complexity.
- `VAULT_FILE` – optional JSON file providing secrets for automated rotation.
- `OAUTH_CLIENT_ID`/`OAUTH_CLIENT_SECRET` – credentials for SSO/OAuth2 login.
- `OAUTH_AUTH_URL`/`OAUTH_TOKEN_URL`/`OAUTH_USERINFO_URL` – endpoints for the OAuth2 provider.
- `ARGON2_TIME_COST`, `ARGON2_MEMORY_COST`, `ARGON2_PARALLELISM` – password hashing parameters.
- `APP_DB_USER`/`APP_DB_PASSWORD` – least-privilege PostgreSQL role created by `init_db.py`.
- `BABEL_DEFAULT_LOCALE`/`BABEL_SUPPORTED_LOCALES` – default and available locales for UI translations.
- `API_TOKEN` – bearer token used to authorize REST and GraphQL requests.
- `ACCOUNTING_URL` – base URL for the accounting connector.
- `S3_RETENTION_DAYS` – optional lifecycle policy for object storage.
- `USE_FAKE_REDIS` – set to `1` during testing to use an in-memory Redis emulator; must be unset in production.

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
- `scripts/monitor_queue.py` checks `/healthz`, queue depth and error rates,
  optionally emailing or posting to Slack when thresholds are exceeded. Set
  `ALERT_EMAIL` and/or `SLACK_WEBHOOK` to enable notifications.

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
Execute `scripts/run_migrations.sh` before starting application services in any deployment pipeline.

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

All templates leverage Bootstrap 5 for responsive design and mobile parity. `Flask-Babel` powers multi-language support; set `BABEL_DEFAULT_LOCALE` and `BABEL_SUPPORTED_LOCALES` to expose additional translations and switch languages via the navbar selector. A global search bar in the navbar queries CRM, inventory, HR, and finance records. A dark-mode toggle with accessible contrast ratios is persisted in `localStorage`. A service worker (`static/js/sw.js`) ensures offline access and queues actions for sync when the connection restores. On first login a brief guided tour highlights navigation and theming. The `/dashboard` route delivers role-based views for employees, clients, and admins.

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
to be used for replication or off-site disaster recovery. On Render, set up a
nightly Cron Job running `python backup.py` with `BACKUP_ENCRYPTION_KEY`
defined so backups are encrypted at rest. Configure an S3 bucket with a
lifecycle policy to expire old backups and reduce storage costs. See
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

## Privacy & Compliance Program

The `/privacy` dashboard summarises ISO/IEC 27001/27701 and SOC 2 readiness, tracks privacy impact assessments, and surfaces upcoming audits.
Refer to [docs/PRIVACY_PROGRAM.md](docs/PRIVACY_PROGRAM.md) for governance roles and KPIs, [docs/DATA_HANDLING_PROCEDURES.md](docs/DATA_HANDLING_PROCEDURES.md) for GDPR/CCPA workflows, and [docs/DPIA_TEMPLATE.md](docs/DPIA_TEMPLATE.md) when evaluating new features.

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
`erp.org_id` session variable, ensuring queries are transparently filtered to the
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

A production-ready WSGI entrypoint (`wsgi.py`), `dockerfile`, and `.env.example`
are provided for running the application in a Gunicorn-backed container. Configure
environment variables as needed and build the container with Docker for
consistent deployments. Kubernetes manifests in `deploy/k8s/` illustrate a
high‑availability setup with readiness probes and horizontal pod autoscaling.
For AWS Elastic Beanstalk, a `dockerrun.aws.json` file references the container image and exposes port 8080 for single-container deployments.
For AWS App Runner source-based deployments, an `apprunner.yaml` file specifies build and start commands. The build stage first upgrades packaging tools with `python3 -m pip install --upgrade pip setuptools wheel` and then installs dependencies from `requirements.lock` using `python3 -m pip install --no-cache-dir -r requirements.lock`. Run `scripts/run_migrations.sh` in the deployment pipeline before launching `gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 8 --timeout 120 wsgi:app`. Ensure the service defines a `DATABASE_URL` (append `?sslmode=require`), `FLASK_SECRET_KEY`, `JWT_SECRETS`, and `REDIS_URL` environment variables.

## Observability & Offline Use

Requests now emit both Prometheus metrics and OpenTelemetry spans. Setting
`OTEL_ENABLED=true` (or `OTEL_EXPORTER_OTLP_ENDPOINT`) instruments Flask,
SQLAlchemy, Redis, Celery, Requests, and logging, enriching JSON logs with
`trace_id`/`span_id` correlation. `/metrics` continues to expose Prometheus
counters and gauges for compatibility.

Additional ServiceMonitors scrape Celery workers, PgBouncer, and Redis as
defined in `deploy/k8s/prometheus.yaml`. Structured logs are emitted to standard
output, while `/status` renders live SLO cards (availability, Apdex, queue
backlog, materialized view freshness) with error budget progress and links to
the [SRE runbook](docs/SRE_RUNBOOK.md).

Key metrics include `graphql_rejects_total` for GraphQL depth/complexity
violations and `audit_chain_broken_total` for tamper‑evident audit log checks.
Database efficiency is monitored through `db_query_count` tests that guard
against N+1 patterns. Cache performance is tracked with `cache_hits_total`,
`cache_misses_total`, and the `cache_hit_ratio` gauge.

The UI registers a service worker (`static/js/sw.js`) to cache core assets and
API responses. User actions are queued in IndexedDB when offline and replayed to
the API once connectivity returns, providing a more resilient mobile experience.
Playwright tests in `tests/test_service_worker_offline.py` exercise these
offline behaviours during continuous integration.

## Security & Load Testing

Run `scripts/security_scan.sh` for static analysis and dependency checks.
Use `scripts/load_test.sh` or a preferred tool to validate performance at target
concurrency levels.

## Performance Benchmarking

Run `python scripts/benchmark.py` against a target URL to measure request
throughput and validate connection pool tuning or scaling changes.

## Current Audit Priorities
The September 2025 audit scored the project **8.3/10** overall and surfaced several high‑leverage fixes. Active efforts focus on:

- Unifying authentication decorators and centralizing permission checks.
- Completing HR recruitment and performance workflows with validations and persistence.
- Replacing ad-hoc SQL in routes with SQLAlchemy models or service layers.
- Guarding unfinished routes with feature flags and clearer messaging.
- Adding structured logging plus health/ready probes for database and broker checks.
- Documenting recovery objectives and executing `scripts/dr_drill.sh` monthly to capture RPO/RTO metrics.
- Monitoring cache hit rate, query counts, and enabling slow-query logging with appropriate indices.
- Automating JWT secret rotation via `JWT_SECRET_ID` using `scripts/rotate_secrets.py` and auditing each rollover.

## Governance & Roadmap

- Refer to `docs/VERSIONING.md` for release numbering and branching conventions.
- Quarterly access recertification steps are outlined in `docs/access_recerts.md`.
- Detailed migration procedures live in `docs/migration_guide.md`.
- User assistance is covered in `docs/in_app_help.md` and `docs/training_tutorials.md`.
- Planned milestones are tracked in `docs/roadmap.md`.
- The phased audit remediation plan lives in `docs/audit_roadmap.md`.
- An in-app `/help` page links to documentation and discussion forums.
- Control mappings to ISO-27001 and Ethiopian data law reside in `docs/control_matrix.md`.
- Quarterly access reviews produce WORM exports via `scripts/access_recert_export.py`.
- Release notes are tracked in `CHANGELOG.md` with rollback steps in `docs/rollback.md`.

## Contributing

- All commits must be GPG-signed.
- Pull requests require approval from owners listed in `codeowners`.
