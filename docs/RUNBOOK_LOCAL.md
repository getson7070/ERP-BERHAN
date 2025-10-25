# ERP-BERHAN — Local Runbook (Port 18000)

## TL;DR
```powershell
cd C:\Users\Alienware\Documents\ERP-BERHAN
# Put these two files into the repo root:
#   - docker-compose.ports-clear.yml
#   - docker-compose.override.yml
# And the scripts/ folder from this pack.

powershell -ExecutionPolicy Bypass -File scripts\reset-dev.ps1 -HardReset

# When web is up, run migrations + seed inside the web container that publishes :18000:
$cid = docker ps --filter "publish=18000" --format "{{.ID}}"
docker exec -it $cid bash -lc "bash -eux scripts/cold_start.sh && python scripts/seed_accounts.py"

# Verify
curl http://localhost:18000/healthz
curl http://localhost:18000/ops/doctor
```
**Test logins**
- Admin: `admin@local.test` / `Dev!23456`
- Employee: `employee@local.test` / `Emp!23456`
- Client: `client@local.test` / `Cli!23456`

## Notes
- We deliberately clear the 8000 host mapping from the base compose and publish only `18000:8000`.
- If port 8000 is still busy on Windows, `reset-dev.ps1` kills the owner process so Compose can start.
- The override also forces the correct Gunicorn app target: `erp.app:create_app()` and adds a healthy Redis service exposed as `cache` to match `REDIS_URL` in the app.
