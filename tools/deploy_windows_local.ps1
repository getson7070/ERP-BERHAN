[CmdletBinding()]
param(
    # Default to the folder where this script lives
    [string]$RepoRoot = $PSScriptRoot,

    # Optional: rebuild images before starting
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve repo root relative to this script
$RepoRoot = (Resolve-Path $RepoRoot).ProviderPath
Write-Host "Using repo root: $RepoRoot" -ForegroundColor Cyan

# Path to the helper script
$helper = Join-Path -Path $RepoRoot -ChildPath "tools\deploy_windows_local.ps1"
if (-not (Test-Path $helper)) {
    throw "Helper script not found at $helper. Make sure tools\deploy_windows_local.ps1 exists."
}

# Forward parameters down to helper
& $helper -RepoRoot $RepoRoot -Rebuild:$Rebuild
