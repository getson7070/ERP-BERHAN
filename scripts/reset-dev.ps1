Param([switch]$HardReset=$false)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\..

Write-Host ">> Cleaning prior containers, networks & ports..." -ForegroundColor Cyan
docker compose down -v --remove-orphans 2>$null | Out-Null
docker rm -f erp-pg, deploy-web-1, deploy-db-1, deploy-redis-1, erp-berhan-redis-1, redis, erp-redis 2>$null | Out-Null
docker network rm erp-berhan_default 2>$null | Out-Null
if ($HardReset) { docker volume rm erp-berhan_erp-pgdata 2>$null | Out-Null }

# Free host ports 8000/18000 if anything is listening
@(8000,18000) | ForEach-Object {
  $pid = (Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
  if ($pid) { try { Stop-Process -Id $pid -Force; Write-Host "stopped PID $pid on port $_" -ForegroundColor DarkGray } catch {} }
}

Write-Host ">> Bringing stack up on :18000 -> container :8000 (with cache)..." -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.ports-clear.yml -f docker-compose.override.yml up -d --build --remove-orphans
if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }

# Apply migrations & seed
$web = (docker compose ps -q web)
if (-not $web) { throw "web container did not start" }
docker compose exec -T web alembic upgrade head
docker compose exec -T web python -m erp.bootstrap_phase1 --seed --admin-email admin@local.test --admin-password 'Dev!23456' --force

# Health
Invoke-RestMethod -Uri http://localhost:18000/healthz -TimeoutSec 30 | Out-String | Write-Host
Invoke-RestMethod -Uri http://localhost:18000/ops/doctor -TimeoutSec 30 | Out-String | Write-Host
