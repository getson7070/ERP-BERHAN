[CmdletBinding()]
param([switch]$HardReset=$false)

$ErrorActionPreference = "Stop"
Write-Host ">> Cleaning prior containers, networks & ports..." -ForegroundColor Cyan

# Free :18000 (host) if busy
$hostPort = 18000
$portProcId = (Get-NetTCPConnection -LocalPort $hostPort -State Listen -ErrorAction SilentlyContinue |
  Select-Object -First 1 -ExpandProperty OwningProcess)
if ($portProcId) {
  Write-Host "Killing process on :$hostPort (PID $portProcId)"
  Stop-Process -Id $portProcId -Force
}

# Clean containers/volumes (wrap via cmd to avoid PS NativeCommandError)
cmd /c "docker compose down -v --remove-orphans 1>NUL 2>NUL"
if ($HardReset) { cmd /c "docker volume rm erp-berhan_erp-pgdata 1>NUL 2>NUL" }

# Build & start (single source of truth)
cmd /c "docker compose up -d --build"
if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }

# Wait for health
$deadline = (Get-Date).AddMinutes(2)
do {
  Start-Sleep -Seconds 2
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:18000/healthz
    if ($resp.StatusCode -eq 200) { break }
  } catch {}
} while ((Get-Date) -lt $deadline)
if (-not $resp -or $resp.StatusCode -ne 200) { throw "healthz failed" }

# Migrate & seed
cmd /c "docker compose exec -T web alembic upgrade head"
cmd /c "docker compose exec -T web python -m erp.bootstrap_phase1 --seed --admin-email admin@local.test --admin-password Dev!23456 --force"

Write-Host ">> Up at http://localhost:18000" -ForegroundColor Green
