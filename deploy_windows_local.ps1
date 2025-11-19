param(
    [switch]$Rebuild,
    [string]$RepoRoot = 'C:\Users\Alienware\Documents\ERP-BERHAN\ERP-BERHAN'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$helper = Join-Path $scriptRoot 'tools\deploy_windows_local.ps1'

if (-not (Test-Path $helper)) {
    throw "Helper script not found at '$helper'. Run 'git pull' to refresh your checkout."
}

& $helper @PSBoundParameters
