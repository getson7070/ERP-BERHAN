# Hotfix v3 helper (optional)
param(
  [string]$Repo = (Get-Location).Path
)

Write-Host "Repo: $Repo"
Set-Location $Repo

# Ensure venv
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
  .\scripts\rebuild_venv.ps1
}

.\.venv\Scripts\Activate.ps1

python .\scripts\autofix_repo_v3.py

pip install -r .\requirements-dev.txt -c .\constraints.txt

pytest -q
