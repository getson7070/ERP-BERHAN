[CmdletBinding()]
param(
    [switch]$Rebuild
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

    Write-Host "Starting docker compose..." -ForegroundColor Yellow
    docker compose up
}
finally {
    Pop-Location
}
