param(
  [Parameter(Mandatory=$true)][string]$RepoPath
)
Write-Host "== ERP-BERHAN Phased Upgrades V2: apply_all_phases.ps1 ==" -ForegroundColor Cyan
$ErrorActionPreference = "Stop"
if (!(Test-Path $RepoPath)) { throw "RepoPath not found: $RepoPath" }

# 1) SocketIO export invariant
$fixer = Join-Path $RepoPath "tools\patch\socketio_export_fix.ps1"
if (Test-Path $fixer) { & $fixer -RepoPath $RepoPath } else { Write-Warning "socketio_export_fix.ps1 missing" }

# 2) Wire MFA blueprint (best-effort, idempotent)
$mfa = Join-Path $RepoPath "tools\patch\wire_mfa_blueprint.ps1"
if (Test-Path $mfa) { & $mfa -RepoPath $RepoPath } else { Write-Warning "wire_mfa_blueprint.ps1 missing" }

# 3) Wire Doctor blueprint (best-effort, idempotent)
$doc = Join-Path $RepoPath "tools\patch\wire_doctor_blueprint.ps1"
if (Test-Path $doc) { & $doc -RepoPath $RepoPath } else { Write-Warning "wire_doctor_blueprint.ps1 missing" }

Write-Host "V2 apply complete. Next: run CI and verify gates." -ForegroundColor Green
