# Deploy Runbook (ERP-BERHAN)

## Preconditions
- CI green on main
- Migration docs present for any schema changes
- Registry scan passes

## Deploy steps
1. Merge to `main`.
2. GitHub Actions triggers CI.
3. If CI passes, Deploy workflow triggers Render deploy hook.
4. Render pulls docker image, runs:
   - entrypoint web: `flask db upgrade` then gunicorn
   - entrypoint worker: `flask db upgrade` then Celery

## Rollback
1. In Render, select previous deploy → Rollback.
2. If migration was destructive:
   - apply downgrade from migration docs
   - restore backup if needed

## Post-deploy checks
- `/healthz` OK
- `/readyz` OK
- Prometheus scrape OK
- Bot dashboard queue depth normal
