# ERP-BERHAN
BERHAN PHARMA

## Environment Variables

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
Deploy behind HTTPS to ensure cookies are protected in transit.
