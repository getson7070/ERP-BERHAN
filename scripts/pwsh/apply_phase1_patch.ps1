
# Apply Phase1 critical patch
param(
  [string]$ZipPath = "C:\Users\Alienware\Downloads\erp-berhan-phase1-critical.zip",
  [string]$RepoPath = "C:\Users\Alienware\Documents\ERP-BERHAN"
)

if (!(Test-Path $ZipPath)) { Write-Error "Zip not found: $ZipPath"; exit 1 }
if (!(Test-Path $RepoPath)) { Write-Error "Repo path not found: $RepoPath"; exit 1 }

$Temp = Join-Path $env:TEMP "erp-phase1-patch"
Remove-Item $Temp -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Path $Temp | Out-Null

Expand-Archive -Path $ZipPath -DestinationPath $Temp -Force

# Overlay files (additive). This will create new files but won't delete existing ones.
robocopy $Temp $RepoPath /E /NFL /NDL /NJH /NJS /NC | Out-Null

# Git add & commit
Push-Location $RepoPath
git add .github/workflows scripts docs .env.example.phase1 2>$null
git commit -m "Phase1: add CI gates (alembic single-head, env-contract, gitleaks) + docs and examples"

Write-Host "Patch applied and committed. Review, then run 'git push origin main' when ready."
Pop-Location
