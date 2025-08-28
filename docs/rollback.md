# Rollback Procedures

1. Identify the failing deployment and record the current image and database
   migration version.
2. Scale down new pods and redeploy the last known-good image.
3. Apply `alembic downgrade` to the recorded migration if the database schema
   changed.
4. Verify health checks and metrics before resuming traffic.
