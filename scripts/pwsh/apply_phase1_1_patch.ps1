
# Apply Phase1.1 patch
param(
  [string]$ZipPath = "C:\Users\Alienware\Downloads\erp-berhan-phase1_1.zip",
  [string]$RepoPath = "C:\Users\Alienware\Documents\ERP-BERHAN"
)

if (!(Test-Path $ZipPath)) { Write-Error "Zip not found: $ZipPath"; exit 1 }
if (!(Test-Path $RepoPath)) { Write-Error "Repo path not found: $RepoPath"; exit 1 }

$Temp = Join-Path $env:TEMP "erp-phase1_1-patch"
Remove-Item $Temp -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Path $Temp | Out-Null

Expand-Archive -Path $ZipPath -DestinationPath $Temp -Force

robocopy $Temp $RepoPath /E /NFL /NDL /NJH /NJS /NC | Out-Null

Push-Location $RepoPath
git add .github/workflows docs
git commit -m "Phase1.1: add pip-audit and Dependabot auto-merge workflows"
Write-Host "Patch applied and committed. Run 'git push origin main' when ready."
Pop-Location
