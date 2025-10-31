Param([int]$Max=3, [switch]$Upgrade)

$ErrorActionPreference = "Stop"
Write-Host "Autogenerate migrations (up to $Max passes)..." -ForegroundColor Cyan

for ($i=1; $i -le $Max; $i++) {
  Write-Host "Pass $i: flask db migrate -m 'autogen pass $i'" -ForegroundColor Yellow
  docker compose exec web flask db migrate -m "autogen pass $i" 2>&1 | Tee-Object -Variable out | Out-Null
  if ($out -match "No changes in schema detected") {
    Write-Host "No changes detected; stopping." -ForegroundColor Green
    break
  }
  if ($Upgrade) {
    Write-Host "Upgrading..." -ForegroundColor Yellow
    docker compose exec web flask db upgrade
  }
}
