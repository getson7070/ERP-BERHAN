# Windows-local helper for running ERP-BERHAN via Docker Desktop
#
# This script assumes the repository lives in
#   C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN
# and that Docker Desktop with the WSL2 backend is installed.
#
# Usage:
#   1. Launch PowerShell *as Administrator*.
#   2. cd into the repository root.
#   3. Execute:  .\tools\deploy_windows_local.ps1
#
# The script performs a basic pre-flight check, brings the stack up,
# runs migrations, and confirms the /healthz endpoint responds.

param(
    [switch]$Rebuild,
    [string]$RepoRoot = 'C:\\Users\\Alienware\\Documents\\ERP-BERHAN\\ERP-BERHAN'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Command {
    param(
        [Parameter(Mandatory)] [string] $Name
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' is not available. Install it before continuing."
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory)] [string] $Label,
        [Parameter(Mandatory)] [scriptblock] $Action
    )
    Write-Host "[STEP] $Label" -ForegroundColor Cyan
    & $Action
    Write-Host "[DONE] $Label`n" -ForegroundColor Green
}

# --- Pre-flight -----------------------------------------------------------------
function Initialize-ComposeCommand {
    if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
        try {
            docker compose version *> $null
            return @{ Kind = 'docker'; Label = 'docker compose' }
        }
        catch {
            Write-Verbose 'docker compose plugin not available, falling back to docker-compose.exe'
        }
    }

    if (Get-Command 'docker-compose' -ErrorAction SilentlyContinue) {
        return @{ Kind = 'docker-compose'; Label = 'docker-compose' }
    }

    throw 'Neither "docker compose" nor "docker-compose" is installed. Install Docker Desktop 3.5+ and retry.'
}

$composeInvoker = $null

Invoke-Step 'Verify required tooling' {
    Assert-Command -Name 'python'
    $composeInvoker = Initialize-ComposeCommand
    Write-Host "Using $($composeInvoker.Label)" -ForegroundColor Yellow
}

function Invoke-Compose {
    param([Parameter(Mandatory)][string[]]$Arguments)

    if ($composeInvoker.Kind -eq 'docker') {
        docker compose @Arguments
    }
    else {
        docker-compose @Arguments
    }
}

Invoke-Step 'Switch to repository root' {
    if (-not (Test-Path $RepoRoot)) {
        throw "Repository path '$RepoRoot' not found. Use -RepoRoot to point at your local clone."
    }
    Set-Location $RepoRoot
}

Invoke-Step 'Copy default env template when missing' {
    $envFile = '.env'
    $template = 'deploy\\example.env'
    if (-not (Test-Path $envFile)) {
        if (-not (Test-Path $template)) {
            throw "Environment template '$template' is missing."
        }
        Copy-Item $template $envFile
    }
}

# --- Containers ------------------------------------------------------------------
$composeFiles = @('docker-compose.yml')
if (Test-Path 'docker-compose.override.yml') {
    $composeFiles += 'docker-compose.override.yml'
}

$composeArgs = @()
foreach ($file in $composeFiles) {
    $composeArgs += @('-f', $file)
}
$composeArgs += 'up'
$composeArgs += if ($Rebuild) { '--build' } else { '--pull=missing' }
$composeArgs += '--remove-orphans'
$composeArgs += '--detach'

Invoke-Step 'Launch application stack' {
    Invoke-Compose -Arguments $composeArgs
}

Invoke-Step 'Run database migrations' {
    Invoke-Compose -Arguments @('exec', 'web', 'flask', 'db', 'upgrade')
}

Invoke-Step 'Seed base data (idempotent)' {
    Invoke-Compose -Arguments @('exec', 'web', 'python', 'init_db.py', '--minimal')
}

Invoke-Step 'Check application health endpoint' {
    Start-Sleep -Seconds 5
    $health = Invoke-WebRequest -Uri 'http://localhost:8000/healthz' -UseBasicParsing
    if ($health.StatusCode -ne 200) {
        throw "/healthz returned status $($health.StatusCode)."
    }
    Write-Host "Health payload:`n$($health.Content)"
}

Invoke-Step 'Tail recent logs (optional stop with Ctrl+C)' {
    Invoke-Compose -Arguments @('logs', '--tail', '50', 'web')
}

Write-Host 'ERP-BERHAN is running at http://localhost:8000' -ForegroundColor Yellow
Write-Host 'Log in with your configured credentials to begin testing.' -ForegroundColor Yellow

