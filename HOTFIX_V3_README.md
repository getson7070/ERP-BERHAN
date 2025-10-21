# ERP Critical Hotfix v3

This hotfix addresses the remaining test collection errors after v2:
- Missing dev deps: **celery**, **prometheus-client**
- `ImportError: cannot import name 'Inventory' from 'erp.models'`
- Robust `celery.schedules` import in `erp/data_retention.py`

## What this drops into your repo
- `scripts/autofix_repo_v3.py` – idempotent patcher:
  - Ensures `celery==5.3.6` and `prometheus-client==0.20.0` are present in `requirements-dev.txt`.
  - Patches `erp/models/__init__.py` to *export* `Inventory`, `Role`, `User` (with safe fallbacks).
  - Patches `erp/data_retention.py` to use a **try/except** import for `celery.schedules.crontab`.
- `scripts/hotfix_v3.ps1` – optional helper to run the steps for you.

## Usage (PowerShell)
```powershell
$repo = "C:\Users\Alienware\Documents\ERP-BERHAN"
$zip  = "C:\Users\Alienware\Downloads\erp_critical_hotfix_v3.zip"

Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force

Set-Location $repo
.\scriptsebuild_venv.ps1
.\.venv\Scripts\Activate.ps1

# Apply patches
python .\scriptsutofix_repo_v3.py

# Reinstall to pick up new dev deps
pip install -r .equirements-dev.txt -c .\constraints.txt

# Run tests
pytest -q
```

## Push to GitHub (fast-forward issue fix)
```powershell
git pull --rebase origin main
git add -A
git commit -m "Hotfix v3: dev deps (celery/prometheus-client) + models exports + celery import guard"
git push origin HEAD:main
```
If you prefer a new branch:
```powershell
git checkout -b fix/hotfix-v3
git push -u origin fix/hotfix-v3
```
