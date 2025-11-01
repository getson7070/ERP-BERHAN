<# 
fix-ports-and-foundations_v2.ps1
Windows PowerShell–compatible (no pwsh required).
- Changes ports 8000 -> 18000 across code/config/docs
- Writes a clean single-source docker-compose.yml
- Updates gunicorn bind to 0.0.0.0:18000
- Archives secondary 'migrations/' tree (keeps 'alembic/' as canonical)
- Cleans junk folders and updates .gitignore
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
  $regex = New-Object System.Text.RegularExpressions.Regex($Pattern, 'Multiline')
  $new = $regex.Replace($raw, $Replacement)
  if ($new -ne $raw) {
    Backup-File -Path $Path
    [IO.File]::WriteAllText($Path, $new, (New-Object System.Text.UTF8Encoding($false)))
  }
}

function Replace-Ports-InTree {
  param([string]$Root)
  Write-Host "» Updating ports $OldPort -> $NewPort across tree…"
  $old = [Regex]::Escape("$OldPort")
  $new = "$NewPort"
  $patterns = @(
    @{ pat = "http://localhost:$old"; rep = "http://localhost:$new" } ,
    @{ pat = "https://localhost:$old"; rep = "https://localhost:$new" } ,
    @{ pat = "0\.0\.0\.0:$old"; rep = "0.0.0.0:$new" } ,
    @{ pat = "127\.0\.0\.1:$old"; rep = "127.0.0.1:$new" } ,
    @{ pat = "\b$old:$old\b"; rep = "$new`:$new" }
  )
  $files = Get-ChildItem -Path $Root -Recurse -File -Include *.yml,*.yaml,*.env,*.py,*.cfg,*.conf,*.ini,*.toml,*.md,*.rst,*.txt,*.ps1,*.sh
  foreach ($f in $files) {
    foreach ($entry in $patterns) {
      Replace-InFile -Path $f.FullName -Pattern $entry.pat -Replacement $entry.rep
    }
  }
}

function Write-CleanCompose {
  param([string]$ComposePath, [int]$Port)
  $content = @'
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["gunicorn","wsgi:app","-k","gthread","-w","3","-b","0.0.0.0:__PORT__","--log-level","info"]
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
      - "__PORT__:__PORT__"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:__PORT__/health"]
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
'@
  $content = $content.Replace('__PORT__', "$Port")
  Backup-File -Path $ComposePath
  [IO.File]::WriteAllText($ComposePath, $content, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "» Wrote clean docker-compose.yml with port $Port"
}

function Update-GunicornPort {
  param([string]$GunicornConf, [int]$Port)
  if (!(Test-Path $GunicornConf)) { return }
  Replace-InFile -Path $GunicornConf -Pattern 'bind\s*=\s*["'']0\.0\.0\.0:\d+["'']' -Replacement ("bind = \"0.0.0.0:{0}\"" -f $Port)
  Write-Host "» Updated gunicorn bind to $Port"
}

function Cleanup-RepoJunk {
  param([string]$Root)
  $toRemove = @(
    ".trash_*","*_backup*","*_bak_*",
    ".venv*","venv*","__pycache__",".pytest_cache",".mypy_cache",".cache",
    "dist","build",".eggs",".idea",".vscode"
  )
  foreach ($pattern in $toRemove) {
    Get-ChildItem -Path $Root -Recurse -Force -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
      try {
        if (Test-Path $_.FullName) {
          Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
          Write-Host "» Removed $($_.FullName)"
        }
      } catch { Write-Warning "Skip removing $($_.FullName): $($_.Exception.Message)" }
    }
  }
}

function Ensure-Gitignore {
  param([string]$Path)
  $rules = @'
# === hygiene added by fix-ports-and-foundations_v2.ps1 ===
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
/_archived_migrations_*/
'@
  if (Test-Path $Path) {
    Backup-File -Path $Path
    Add-Content -LiteralPath $Path -Value $rules
  } else {
    [IO.File]::WriteAllText($Path, $rules, (New-Object System.Text.UTF8Encoding($false)))
  }
  Write-Host "» .gitignore updated"
}

function Consolidate-Migrations {
  param([string]$ProjectRoot)
  $alembic = Join-Path $ProjectRoot "alembic"
  $migrations = Join-Path $ProjectRoot "migrations"
  if (Test-Path $migrations) {
    $archive = Join-Path $ProjectRoot ("_archived_migrations_" + (Get-Date -Format 'yyyyMMdd_HHmm'))
    New-Item -ItemType Directory -Force -Path $archive | Out-Null
    Move-Item -LiteralPath $migrations -Destination (Join-Path $archive "migrations") -Force
    Write-Host "» Archived 'migrations' to $archive"
  }
  $todo = @'
# MIGRATIONS_TODO
There were multiple Alembic heads earlier. After this cleanup, run a one-time merge:
1) docker compose run --rm web bash -lc "alembic heads"
2) docker compose run --rm web bash -lc "alembic merge -m 'merge heads' <head1> <head2> [<headN>]"
3) docker compose run --rm web bash -lc "alembic upgrade head"
'@
  [IO.File]::WriteAllText((Join-Path $ProjectRoot "MIGRATIONS_TODO.txt"), $todo, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "» Wrote MIGRATIONS_TODO.txt"
}

# --- Execution ---
$proj = Resolve-Path -LiteralPath $Repo
$root = $proj.ProviderPath

$compose = Join-Path $root "docker-compose.yml"
$gunicornConf = Join-Path $root "gunicorn.conf.py"

Replace-Ports-InTree -Root $root
Write-CleanCompose -ComposePath $compose -Port $NewPort
Update-GunicornPort -GunicornConf $gunicornConf -Port $NewPort
Consolidate-Migrations -ProjectRoot $root
Cleanup-RepoJunk -Root $root
Ensure-Gitignore -Path (Join-Path $root ".gitignore")

Write-Host "`n✅ Done."
Write-Host "Next:"
Write-Host "  - Rebuild and start: docker compose build --no-cache && docker compose up -d"
Write-Host "  - One-time: inside 'web' container, follow MIGRATIONS_TODO.txt to merge heads"