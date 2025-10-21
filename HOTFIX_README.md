# ERP Critical Hotfix v2

## What changed from v1
- Added missing dev/test dependencies (`redis`, `Flask-Login`, `Flask-WTF`, `WTForms`, `pyotp`, `boto3`, `requests`, `psycopg2-binary`).
- Stronger `autofix_repo.py` that **forces** `from __future__ import annotations` to the top of `erp/data_retention.py` and re-exports `Inventory`, `User`, `Role` from `erp.db`.
- Keeps blueprint export for `delete_item`, and package-root exports for `socketio` and metrics.

## Steps (PowerShell)
```powershell
$repo = "C:\Users\Alienware\Documents\ERP-BERHAN"
$zip  = "C:\Users\Alienware\Downloads\erp_critical_hotfix_v2.zip"

Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
Set-Location $repo
.\scriptsebuild_venv.ps1
.\.venv\Scripts\Activate.ps1

python .\scriptsutofix_repo.py
pytest -q
```

If `git push` is rejected:
```powershell
git pull --rebase origin main
git push origin HEAD:main
```
