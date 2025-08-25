# ERP-BERHAN
BERHAN PHARMA

## Environment Variables

The application pulls configuration from environment variables. Key settings include:

- `FLASK_SECRET_KEY` – secret key for session and CSRF protection.
- `DATABASE_URL` – PostgreSQL connection string used by SQLAlchemy.
- `ADMIN_USERNAME`/`ADMIN_PASSWORD` – credentials used for initial admin seeding.
- `TOTP_ISSUER` – issuer name shown in authenticator apps for MFA codes.

The analytics module uses Celery for scheduled reporting. Configure the broker
and result backend via the following environment variables:

- `CELERY_BROKER_URL` – URL of the message broker (default
  `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` – URL of the result backend (default
  `redis://localhost:6379/0`)

Set these variables in your deployment environment to point Celery to your
Redis instance.

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

## Backups

The `backup.py` helper creates timestamped database backups. PostgreSQL and
MySQL connections are dumped via `pg_dump` and `mysqldump`, allowing the dumps
to be used for replication or off-site disaster recovery.

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
secret rotation.

### Materialized Views

Key performance indicators are pre-aggregated in the `kpi_sales` materialized
view. A Celery beat job periodically executes `REFRESH MATERIALIZED VIEW
CONCURRENTLY kpi_sales` and pushes updates to connected dashboards over
WebSockets for near real-time visibility.

## Tender Lifecycle

Tenders progress through defined workflow states culminating in automatic
transitions to **Evaluated** and **Awarded**. When a tender is evaluated the
status becomes *Evaluated*; recording a winning supplier and date moves it to
*Awarded* and stores the `awarded_to` and `award_date` fields.

## Deployment

A production-ready WSGI entrypoint (`wsgi.py`), `Dockerfile`, and `.env.example`
are provided for running the application in a Gunicorn-backed container. Configure
environment variables as needed and build the container with Docker for
consistent deployments.

## Observability & Offline Use

Requests are instrumented with Prometheus metrics and exposed at `/metrics` for
collection by a monitoring system. Structured logs are emitted to standard
output to aid in tracing and alerting.

The UI registers a service worker (`static/js/sw.js`) to cache core assets and
API responses. User actions are queued in IndexedDB when offline and replayed to
the API once connectivity returns, providing a more resilient mobile experience.
