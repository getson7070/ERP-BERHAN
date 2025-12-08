[CmdletBinding()]
param(
    [switch]$Rebuild,
    [switch]$SkipMigrationCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path $PSScriptRoot).ProviderPath
Write-Host "Using repo root: $RepoRoot" -ForegroundColor Cyan

Push-Location $RepoRoot

try {
    if ($Rebuild) {
        Write-Host "Rebuilding Docker images..." -ForegroundColor Yellow
        docker compose build
    }

    if (-not $SkipMigrationCheck) {
        Write-Host "Running migration preflight (no DB required)..." -ForegroundColor Yellow
        docker compose -f docker-compose.migrate.yml run --rm migrate python tools/check_migration_health.py
    }

    Write-Host "Starting docker compose..." -ForegroundColor Yellow
    docker compose up
}
finally {
    Pop-Location
}
