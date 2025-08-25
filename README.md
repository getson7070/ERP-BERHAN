# ERP-BERHAN
BERHAN PHARMA

## Environment Variables

The application pulls configuration from environment variables. Key settings include:

- `FLASK_SECRET_KEY` – secret key for session and CSRF protection.
- `DATABASE_PATH` – path to the SQLite database file (default `erp.db`).
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

## Security

Session cookies are configured with `Secure`, `HttpOnly` and `SameSite=Lax`.
[`Flask-Talisman`](https://github.com/GoogleCloudPlatform/flask-talisman) enforces HTTPS
and sets modern security headers; ensure the app is served over TLS.

## Backups

The `backup.py` helper creates timestamped database backups. SQLite databases
are copied directly while PostgreSQL and MySQL connections are dumped via
`pg_dump` and `mysqldump`. These dumps can be used for replication or off-site
disaster recovery.

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
