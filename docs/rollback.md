# Rollback Procedures

1. Identify the failing deployment and record the current image and database
   migration version.
2. Gradually shift a small percentage of traffic (canary) to the new release while monitoring metrics.
3. Scale down new pods and redeploy the last known-good image if error budgets are exceeded.
4. Apply `alembic downgrade` to the recorded migration if the database schema
   changed.
5. Verify health checks and metrics before resuming traffic.
