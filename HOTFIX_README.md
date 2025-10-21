# ERP‑BERHAN — Critical Hotfix Pack

This ZIP contains *surgical* fixes to unblock your test run and CI by:
- repairing imports/constants the tests expect,
- providing a Socket.IO instance at package root,
- adding a safe dead‑letter handler,
- fixing a `from __future__` placement issue,
- adding minimal shims for `erp.db` and inventory blueprint exports,
- giving you known‑good dependency pins and a clean venv rebuild script.

## Quick apply (PowerShell)

```powershell
$zip = "C:\Users\Alienware\Downloads\erp_critical_hotfix.zip"
$repo = "C:\Users\Alienware\Documents\ERP-BERHAN"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force

Set-Location $repo
.\scripts\rebuild_venv.ps1
.\.venv\Scripts\Activate.ps1
python .\scripts\autofix_repo.py
pytest -q

git add -A
git commit -m "Critical hotfix: pins + autopatched symbols and future-import placement"
git push origin main
```
