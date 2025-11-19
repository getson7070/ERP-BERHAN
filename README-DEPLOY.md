# ERP-BERHAN — Deployability & Hardening (updated 2025-10-29 12:45:46 UTC)

## TL;DR
- **Host port** is parameterized: set `HOST_PORT=8010` in `.env` (Windows-friendly).  
- **Dev discovery**: `ERP_AUTO_REGISTER=1` to log import/url_prefix issues and register all blueprints.  
- **Prod**: freeze explicit blueprint list, set `ERP_AUTO_REGISTER=0`.  
- **Migrations**: run autogenerate until clean; single Alembic head enforced in CI.  
- **Per-blueprint limits**: set JSON mapping via `ERP_BP_LIMITS` (e.g., `{"auth":"10/minute;100/day"}`).  
- **Security**: CSRF enabled, cookies hardened, optional CSP/HSTS if Talisman installed.  
- **Hygiene**: `.dockerignore` excludes `.venv*`, `__pycache__`, backups.

## Quick Start
```powershell
# 0) Prepare env
Copy-Item .env.example .env -Force
notepad .env   # set SECRET_KEY, HOST_PORT, ERP_AUTO_REGISTER=1 (dev)

# 1) Build & run
docker compose build
docker compose up -d --remove-orphans
docker compose logs -f web
Invoke-WebRequest http://localhost:%HOST_PORT%/healthz | Select-Object -ExpandProperty Content

# 2) Migrations (repeat until clean)
docker compose exec web flask db migrate -m "autogen pass 1"
docker compose exec web flask db upgrade

# 3) Freeze blueprints for prod
docker compose exec web python -m erp.tools.freeze_blueprints  # writes erp/blueprints_explicit.py
# edit erp/blueprints_explicit.py to confirm url_prefix per blueprint

# 4) Switch to prod-like
# In .env: set ERP_AUTO_REGISTER=0
docker compose up -d
```

## Windows + Docker Desktop Walkthrough
Need a detailed, Windows-specific flow (PowerShell, WSL 2 backend, explicit host paths, verification commands, and troubleshooting tips)?
Follow [`docs/docker_desktop_guide.md`](docs/docker_desktop_guide.md) for the complete procedure tailored to a checkout at `C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN`.

**Quick helper script:**

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
cd C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN
./deploy_windows_local.ps1 -Rebuild
```

If your checkout lives somewhere else, append `-RepoRoot "D:\sandbox\ERP-BERHAN"` to point the helper at the right folder.  The wrapper automatically falls back to `docker-compose.exe` when the Compose V2 plugin is unavailable.

## DB Snapshot
```powershell
PowerShell -ExecutionPolicy Bypass -File .\tools\db_snapshot.ps1
```
Outputs `snapshots\erp_<module 'datetime' from '/usr/local/lib/python3.11/datetime.py'>.sql`.
