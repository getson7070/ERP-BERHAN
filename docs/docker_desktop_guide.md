# Docker Desktop Deployment Guide (Windows PowerShell)

This guide walks through deploying ERP-BERHAN on Docker Desktop for Windows when the repository lives at `C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN`. Follow the sequence end-to-end to ensure dependencies, services, and tests work together.

## 1. Prerequisites
- **Windows 11/10 Pro** with hardware virtualization enabled in BIOS/UEFI.
- **Docker Desktop** v4.30 or newer with the WSL 2 backend enabled.
- **PowerShell 7+** (the commands below assume the default execution policy allows local scripts; run `Set-ExecutionPolicy -Scope Process Bypass` if needed).
- **Git** installed so that line endings remain LF inside the repo (set `git config core.autocrlf false`).

## 2. Open a PowerShell session in the project folder
```powershell
cd "C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN"
```
If you stored environment secrets elsewhere, load them now (for example, `Get-Content $HOME\.erp\secrets.ps1 | Invoke-Expression`).

## 3. Prepare environment variables
1. Copy the sample environment file:
   ```powershell
   Copy-Item .env.example .env -Force
   ```
2. Update `.env` with secure values:
   - `SECRET_KEY`, `SECURITY_PASSWORD_SALT`
   - `DATABASE_URL=postgresql+psycopg2://erp:erp@db:5432/erp`
   - `HOST_PORT=8010` (or another open port)
   - `ERP_AUTO_REGISTER=1` for development so blueprints self-register.
3. (Optional) Append overrides for mail, Celery, Redis, or rate limiting as needed.

## 4. Build and run the stack
```powershell
# Clean dangling resources from previous runs
wsl docker compose down --remove-orphans
wsl docker system prune --volumes --force

# Build and start the core services
wsl docker compose --profile desktop -f docker-compose.yml up -d --build

# Tail logs until the health check reports ready
wsl docker compose logs -f web
```
If you use the default profile only, omit `--profile desktop`.

## 5. Initialize and migrate the database
```powershell
wsl docker compose exec web flask db upgrade
wsl docker compose exec web flask db stamp head
wsl docker compose exec web flask db migrate --message "verify_desktop"
wsl docker compose exec web flask db upgrade
```
Seeding demo data:
```powershell
wsl docker compose exec web python init_db.py --demo
```

## 6. Verify application health and module wiring
```powershell
$env:HOST_PORT = (Get-Content .env | Where-Object { $_ -match '^HOST_PORT' }).Split('=')[1]
Invoke-RestMethod -Uri "http://localhost:$env:HOST_PORT/healthz"
Invoke-RestMethod -Uri "http://localhost:$env:HOST_PORT/api/meta/blueprints"
```
Check CRM/finance routes quickly:
```powershell
Invoke-WebRequest "http://localhost:$env:HOST_PORT/crm/" | Select-Object -ExpandProperty StatusDescription
Invoke-WebRequest "http://localhost:$env:HOST_PORT/finance/" | Select-Object -ExpandProperty StatusDescription
```

## 7. Run the automated test suite inside Docker
```powershell
wsl docker compose exec web pytest -q
```
For targeted checks (blueprint registration, routes):
```powershell
wsl docker compose exec web pytest tests/test_blueprint_registration.py tests/test_core_modules.py -q
```

## 8. Access the UI
Open a browser to `http://localhost:8010/` (or your chosen host port). Ensure you can:
- Sign in, create demo records, and navigate CRM, HR, finance, and analytics dashboards.
- Submit forms (feedback, orders) and observe real-time updates in the dashboard.

## 9. Shut down and clean up
```powershell
wsl docker compose down
wsl docker volume ls | Where-Object { $_.Name -like 'erp*' } | ForEach-Object { wsl docker volume rm $_.Name }
```
If you want to keep Postgres data, skip the volume removal step.

## 10. Troubleshooting tips
- **Port conflicts**: Change `HOST_PORT` in `.env` and restart `docker compose`.
- **Stuck containers**: Run `wsl docker compose ps -a` to spot crashes, then inspect logs via `wsl docker compose logs <service>`.
- **Dependency rebuilds**: `wsl docker compose build --no-cache web` when `requirements*.txt` changes.
- **File permission mismatches**: In PowerShell, run `wsl sudo chown -R $(wsl whoami):$(wsl whoami) /workspace/ERP-BERHAN` inside WSL to sync ownership.
- **Database resets**: `wsl docker compose exec db dropdb erp -U postgres; wsl docker compose exec db createdb erp -U postgres` followed by migrations.

## 11. Hardening checklist before production
- Set `ERP_AUTO_REGISTER=0` after capturing a frozen blueprint manifest (`python -m erp.tools.freeze_blueprints`).
- Enable HTTPS termination (Traefik/Nginx) and configure CSP/HSTS headers.
- Rotate default passwords and configure SSO or OAuth for admin accounts.
- Enable backups using `tools/db_snapshot.ps1` and store artifacts securely.
