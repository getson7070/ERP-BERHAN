Param(
  [string]$DbName = "erp",
  [string]$User = "erp"
)
$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$snap = "snapshots\erp_$ts.sql"
New-Item -ItemType Directory -Force -Path "snapshots" | Out-Null
# -T disables pseudo-TTY so piping works on Windows
docker compose exec -T erp-db pg_dump -U $User $DbName | Out-File -Encoding ascii $snap
Write-Host "Snapshot wrote to $snap" -ForegroundColor Green
