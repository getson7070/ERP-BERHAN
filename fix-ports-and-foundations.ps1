<# 
fix-ports-and-foundations.ps1
Purpose:
- Change service port from 8000 to 18000 across code, configs, docs
- Normalize docker-compose to a single, clean definition
- Update gunicorn bind to 0.0.0.0:18000 and healthchecks
- Remove obvious duplicate/backup/trash directories
- Consolidate to a single Alembic root (keep `alembic/`, archive `migrations/`)
- Add .gitignore rules for caches/venvs/backups
- Leave a MIGRATIONS_TODO note for a one-time Alembic "merge heads" step

Usage:
  pwsh -File .\fix-ports-and-foundations.ps1 -Repo "C:\Users\Alienware\Documents\ERP-BERHAN"
#>

param(
  [Parameter(Mandatory=$true)]
  [string]$Repo,
  [int]$NewPort = 18000,
  [int]$OldPort = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Backup-File { 
  param([string]$Path)
  if (Test-Path $Path) { 
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    Copy-Item $Path "$Path.bak_$ts" -Force 
  }
}

function Replace-InFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Pattern,
    [Parameter(Mandatory=$true)][string]$Replacement
  )
  if (!(Test-Path $Path)) { return }
  $raw = Get-Content -Raw -LiteralPath $Path
  $new = [System.Text.RegularExpressions.Regex]::Replace($raw, $Pattern, $Replacement, 
    [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if ($new -ne $raw) {
    Backup-File -Path $Path
    [IO.File]::WriteAllText($Path, $new, (New-Object System.Text.UTF8Encoding($false)))
  }
}

function Replace-Ports-InTree {
  param([string]$Root)
  Write-Host "Â» Updating ports $OldPort -> $NewPort in files (compose, docs, configs, code)â€¦"
  $patterns = @(
    # URLs and binds
    "http://localhost:$OldPort",
    "https://localhost:$OldPort",
    "0\.0\.0\.0:$OldPort",
    "127\.0\.0\.1:$OldPort",
    # YAML ports: "18000:18000" â†’ "18000:18000"
    "(['""]?)$OldPort:($OldPort)\1"
  )
  $replacements = @(
    "http://localhost:$NewPort",
    "https://localhost:$NewPort",
    "0.0.0.0:$NewPort",
    "127.0.0.1:$NewPort",
    "$NewPort`:$NewPort"
  )

  $files = Get-ChildItem -Path $Root -Recurse -File -Include *.yml,*.yaml,*.env,*.py,*.cfg,*.conf,*.ini,*.toml,*.md,*.rst,*.txt,*.ps1,*.sh
  foreach ($f in $files) {
    for ($i=0; $i -lt $patterns.Count; $i++) {
      Replace-InFile -Path $f.FullName -Pattern $patterns[$i] -Replacement $replacements[$i]
    }
  }
}

function Write-CleanCompose {
  param([string]$ComposePath, [int]$Port)
  $content = @"
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["gunicorn","wsgi:app","-k","gthread","-w","3","-b","0.0.0.0:$Port","--log-level","info"]
    environment:
      FLASK_APP: erp:create_app
      FLASK_ENV: production
      DATABASE_URL: postgresql+psycopg://erp:erp@db:5432/erp
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "$Port:$Port"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:$Port/health"]
      interval: 30s
      timeout: 10s
      retries: 5
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["celery","-A","erp.celery_app.celery_app","worker","--loglevel=info"]
    environment:
      DATABASE_URL: postgresql+psycopg://erp:erp@db:5432/erp
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: erp
      POSTGRES_PASSWORD: erp
      POSTGRES_DB: erp
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp -d erp"]
      start_period: 20s
      interval: 10s
      timeout: 5s
      retries: 10
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: ["redis-server","--appendonly","yes"]
    healthcheck:
      test: ["CMD","redis-cli","ping"]
      interval: 10s
      timeout: 5s
      retries: 10
    volumes:
      - redis_data:/data

volumes:
  db_data: {}
  redis_data: {}
"@
  Backup-File -Path $ComposePath
  [IO.File]::WriteAllText($ComposePath, $content, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "Â» Wrote clean docker-compose.yml with port $Port"
}

function Update-GunicornPort {
  param([string]$GunicornConf, [int]$Port)
  if (!(Test-Path $GunicornConf)) { return }
  Replace-InFile -Path $GunicornConf -Pattern 'bind\s*=\s*["'']0\.0\.0\.0:\d+["'']' -Replacement "bind = `"0.0.0.0:$Port`""
  Write-Host "Â» Updated gunicorn bind to $Port"
}

function Cleanup-RepoJunk {
  param([string]$Root)
  $toRemove = @(
    ".trash_*","*_backup*","*_bak_*",
    ".venv*","venv*","__pycache__",".pytest_cache",".mypy_cache",".cache",
    "dist","build",".eggs",".idea",".vscode"
  )
  foreach ($pattern in $toRemove) {
    Get-ChildItem -Path $Root -Recurse -Force -Filter $pattern | ForEach-Object {
      try {
        if (Test-Path $_.FullName) {
          Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
          Write-Host "Â» Removed $($_.FullName)"
        }
      } catch { Write-Warning "Skip removing $($_.FullName): $($_.Exception.Message)" }
    }
  }
}

function Ensure-Gitignore {
  param([string]$Path)
  $rules = @"
# === hygiene added by fix-ports-and-foundations.ps1 ===
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.cache/
dist/
build/
.eggs/
.trash_*/
*_backup*/
*_bak_*/
.idea/
.vscode/
.env
.env.*
/ERP-BERHAN/_archived_migrations_*/
"@
  if (Test-Path $Path) {
    Backup-File -Path $Path
    Add-Content -LiteralPath $Path -Value $rules
  } else {
    [IO.File]::WriteAllText($Path, $rules, (New-Object System.Text.UTF8Encoding($false)))
  }
  Write-Host "Â» .gitignore updated"
}

function Consolidate-Migrations {
  param([string]$ProjectRoot)
  $alembic = Join-Path $ProjectRoot "alembic"
  $migrations = Join-Path $ProjectRoot "migrations"
  if (Test-Path $migrations) {
    $archive = Join-Path $ProjectRoot ("_archived_migrations_" + (Get-Date -Format 'yyyyMMdd_HHmm'))
    New-Item -ItemType Directory -Force -Path $archive | Out-Null
    Move-Item -LiteralPath $migrations -Destination (Join-Path $archive "migrations") -Force
    Write-Host "Â» Archived 'migrations' to $archive"
  }
  # Drop a TODO note for merge-heads
  $todo = @"
# MIGRATIONS_TODO
There were multiple Alembic heads earlier. After this cleanup, run a one-time merge:
1) docker compose run --rm web bash -lc "alembic heads"
2) docker compose run --rm web bash -lc "alembic merge -m 'merge heads' <head1> <head2> [<headN>]"
3) docker compose run --rm web bash -lc "alembic upgrade head"
"@
  [IO.File]::WriteAllText((Join-Path $ProjectRoot "MIGRATIONS_TODO.txt"), $todo, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "Â» Wrote MIGRATIONS_TODO.txt"
}

# --- Execution ---
$proj = Resolve-Path -LiteralPath $Repo
$root = $proj.ProviderPath

# 1) Normalize core paths
$compose = Join-Path $root "docker-compose.yml"
$gunicornConf = Join-Path $root "gunicorn.conf.py"

# 2) Replace ports across the tree
Replace-Ports-InTree -Root $root

# 3) Overwrite with a clean, canonical docker-compose.yml
Write-CleanCompose -ComposePath $compose -Port $NewPort

# 4) Update gunicorn bind
Update-GunicornPort -GunicornConf $gunicornConf -Port $NewPort

# 5) Consolidate migrations (archive secondary tree)
Consolidate-Migrations -ProjectRoot $root

# 6) Remove obvious junk/backups/venvs/caches
Cleanup-RepoJunk -Root $root

# 7) Ensure .gitignore includes hygiene rules
Ensure-Gitignore -Path (Join-Path $root ".gitignore")

Write-Host "`nâœ… Done."
Write-Host "Next:"
Write-Host "  - Rebuild and start: docker compose build --no-cache && docker compose up -d"
Write-Host "  - Inside the 'web' container, finish the Alembic merge per MIGRATIONS_TODO.txt"

