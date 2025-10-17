param([string]$RepoRoot = ".")
$RepoRoot = (Resolve-Path $RepoRoot).Path

Write-Host "[1/6] Copying ops files (gunicorn, wsgi_eventlet, render snippet)..."
Copy-Item "$RepoRoot\patches\ops\gunicorn.conf.py" "$RepoRoot\gunicorn.conf.py" -Force
Copy-Item "$RepoRoot\patches\ops\wsgi_eventlet.py" "$RepoRoot\wsgi_eventlet.py" -Force
New-Item -ItemType Directory -Force -Path "$RepoRoot\ops" | Out-Null
Copy-Item "$RepoRoot\patches\ops\render.patch.yaml" "$RepoRoot\ops\render.patch.yaml" -Force

Write-Host "[2/6] Hardening Alembic config..."
Copy-Item "$RepoRoot\patches\alembic.ini" "$RepoRoot\alembic.ini" -Force
Copy-Item "$RepoRoot\patches\migrations\env.py" "$RepoRoot\migrations\env.py" -Force

Write-Host "[3/6] Adding security & blueprints/models..."
New-Item -ItemType Directory -Force -Path "$RepoRoot\erp\security" | Out-Null
New-Item -ItemType Directory -Force -Path "$RepoRoot\erp\blueprints" | Out-Null
New-Item -ItemType Directory -Force -Path "$RepoRoot\erp\models" | Out-Null
New-Item -ItemType Directory -Force -Path "$RepoRoot\bots" | Out-Null
New-Item -ItemType Directory -Force -Path "$RepoRoot\scripts" | Out-Null
Copy-Item "$RepoRoot\patches\erp\security\input_sanitizer.py" "$RepoRoot\erp\security\input_sanitizer.py" -Force
Copy-Item "$RepoRoot\patches\erp\blueprints\*" "$RepoRoot\erp\blueprints\" -Force
Copy-Item "$RepoRoot\patches\erp\models\*" "$RepoRoot\erp\models\" -Force
Copy-Item "$RepoRoot\patches\bots\slack_app.py" "$RepoRoot\bots\slack_app.py" -Force

Write-Host "[4/6] Adding helper scripts & tests..."
Copy-Item "$RepoRoot\patches\scripts\*" "$RepoRoot\scripts\" -Force
New-Item -ItemType Directory -Force -Path "$RepoRoot\tests" | Out-Null
Copy-Item "$RepoRoot\patches\tests\*" "$RepoRoot\tests\" -Force

Write-Host "[5/6] Append new requirements..."
$append = Get-Content "$RepoRoot\patches\requirements.append.txt"
$reqPath = "$RepoRoot\requirements.txt"
if (!(Test-Path $reqPath)) { New-Item $reqPath -ItemType File | Out-Null }
foreach ($line in $append) {
  if ($line.Trim().Length -gt 0) {
    if (-not (Select-String -Path $reqPath -Pattern ("^" + [regex]::Escape($line) + "$") -SimpleMatch -Quiet)) {
      Add-Content $reqPath $line
    }
  }
}

Write-Host "[6/6] Done. Next:"
Write-Host " - pip install -r requirements.txt"
Write-Host " - bash scripts/create_migration_and_upgrade.sh"
Write-Host " - set env: GUNICORN_WORKER_CLASS=eventlet, PROMETHEUS_MULTIPROC_DIR=/tmp/prom"
Write-Host " - point your process to 'wsgi_eventlet:app'"
