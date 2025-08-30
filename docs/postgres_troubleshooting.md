# PostgreSQL Connectivity Troubleshooting

If tests or the application fail with `connection refused` errors, ensure the local
PostgreSQL service is installed and running.

1. Install and initialize the server using the bundled script:
   ```bash
   scripts/setup_postgres.sh
   ```
2. Verify the database accepts connections:
   ```bash
   pg_isready -d postgresql://postgres:postgres@localhost:5432/erp?sslmode=require
   ```
3. Run migrations and tests:
   ```bash
   alembic upgrade head
   pytest
   ```

These steps provision the `erp` database and set the default password so future
runs succeed without manual intervention.
