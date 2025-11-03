# tools\fix-all.ps1
$ErrorActionPreference = 'Stop'
$ts   = Get-Date -Format yyyyMMdd_HHmmss
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $repo  # go one level up (â€¦\ERP-BERHAN)

function Backup($p){ if(Test-Path $p){ Copy-Item $p ($p + ".bak_$ts") -Force } }

# Paths
$df    = Join-Path $repo 'Dockerfile'
$dc    = Join-Path $repo 'docker-compose.yml'
$rin   = Join-Path $repo 'requirements.in'
$rlock = Join-Path $repo 'requirements.lock'

Set-Location $repo

# Backups
Backup $df; Backup $dc; Backup $rin; Backup $rlock

# Ensure requirements.in
if(-not (Test-Path $rin)){
  @(
    'Flask==3.0.3'
    'Flask-SQLAlchemy==3.1.1'
    'SQLAlchemy==2.0.32'
    'Flask-Migrate==4.0.7'
    'alembic==1.13.2'
    'gunicorn==21.2.0'
    'psycopg[binary]==3.2.12'
    'redis==5.0.8'
    'celery==5.5.3'
    'Flask-Limiter==4.0.0'
    'Flask-WTF==1.2.1'
    'Flask-Login==0.6.3'
    'Flask-SocketIO==5.3.6'
    'python-dotenv==1.0.1'
    'requests==2.32.5'
    'sentry-sdk[flask]==2.13.0'
    'flask-talisman==1.1.0'
    'argon2-cffi==23.1.0'
  ) | Set-Content -Encoding UTF8 -LiteralPath $rin
}

# Lockfile
python -m pip install -q --upgrade pip pip-tools | Out-Null
python -m piptools compile $rin --generate-hashes -o $rlock
if(-not (Test-Path $rlock)){ throw "requirements.lock not created" }

# Dockerfile (create if missing)
if(-not (Test-Path $df)){
  @(
    'FROM python:3.11-slim'
    'ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=erp:create_app'
    'RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates && rm -rf /var/lib/apt/lists/*'
    'WORKDIR /app'
    'COPY requirements.lock /app/requirements.lock'
    'RUN python -m pip install --upgrade pip && python -m pip install --require-hashes -r requirements.lock'
    'COPY . /app'
    'CMD ["gunicorn","-c","gunicorn.conf.py","wsgi:app"]'
  ) | Set-Content -Encoding UTF8 -LiteralPath $df
}

# Dockerfile patch (idempotent)
$d = Get-Content $df -Raw
$d = $d -replace '(?ms)COPY\s+requirements\.txt.*','COPY requirements.lock /app/requirements.lock'
$d = $d -replace '(?ms)RUN\s+pip\s+install\s+-r\s+requirements\.txt','RUN python -m pip install --require-hashes -r requirements.lock'
if($d -notmatch 'FLASK_APP='){
  $d = $d -replace 'WORKDIR\s+/app', ('WORKDIR /app' + [Environment]::NewLine + 'ENV FLASK_APP=erp:create_app')
}
if($d -notmatch 'ca-certificates'){
  $d = $d -replace 'apt-get install -y --no-install-recommends([^\r\n]+)','apt-get install -y --no-install-recommends$1 curl ca-certificates'
}
Set-Content -Encoding UTF8 $df $d

# Compose checks & light patch (no huge regex gymnastics)
if(-not (Test-Path $dc)){ throw "docker-compose.yml not found at $dc" }
$y = Get-Content $dc -Raw
$y = $y -replace '^\s*version:.*\r?\n',''  # remove legacy version line

if($y -notmatch '(?ms)^\s*web:'){
  throw "'web' service not found in docker-compose.yml"
}

if($y -notmatch '(?ms)^\s*web:.*?\n\s*ports:\s*\r?\n\s*-\s*"8080:8000"'){
  if($y -match '(?ms)^\s*web:.*?\n\s*ports:\s*\r?\n'){
    $y = [regex]::Replace($y,'(?ms)(^\s*web:.*?\n\s*ports:\s*\r?\n)\s*-\s*.*','$1      - "8080:8000"')
  } else {
    $y = [regex]::Replace($y,'(?ms)(^\s*web:.*?\r?\n)(\s*[a-z]|$)','$1    ports:' + "`r`n" + '      - "8080:8000"' + "`r`n" + '$2')
  }
}

if($y -notmatch '(?ms)^\s*web:.*?\n\s*depends_on:'){
  $y = [regex]::Replace($y,'(?ms)(^\s*web:.*?\n\s*ports:.*?\r?\n)','$1    depends_on:' + "`r`n" + '      - db' + "`r`n" + '      - redis' + "`r`n")
}

if($y -notmatch '(?ms)^\s*web:.*?\n\s*healthcheck:'){
  $y = [regex]::Replace($y,'(?ms)(^\s*web:.*?\n\s*ports:.*?\r?\n)','$1    healthcheck:' + "`r`n" +
    '      test: ["CMD","curl","-f","http://localhost:18000/healthz"]' + "`r`n" +
    '      interval: 10s' + "`r`n" +
    '      timeout: 3s' + "`r`n" +
    '      retries: 10' + "`r`n")
}
Set-Content -Encoding UTF8 $dc $y

# Clean & build
docker compose down --remove-orphans | Out-Null
docker container prune -f | Out-Null
docker image prune -f | Out-Null
# optional: nuke any local ERP volumes to get a fresh DB
docker volume ls --format '{{.Name}}' | Where-Object { $_ -match '^erp-berhan_' } | ForEach-Object { docker volume rm $_ 2>$null | Out-Null }

docker compose build
docker compose up -d db redis

# Wait for DB
$deadline = (Get-Date).AddMinutes(2)
while((Get-Date) -lt $deadline){
  try{
    docker compose exec -T db pg_isready -U erp -d erp | Select-String 'accepting connections' | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 3
  }
}

# Alembic heads & upgrade
$headsOut = docker compose run --rm web alembic heads 2>$null
$headIds  = @()
if($headsOut){ ($headsOut -split "`r?`n") | ForEach-Object { if($_ -match '^\s*([0-9a-f]+)\b'){ $headIds += $Matches[1] } } }
if($headIds.Count -gt 1){
  Write-Host "Merging heads: $($headIds -join ' ')"
  docker compose run --rm web alembic merge -m 'unify heads' $headIds
} else {
  Write-Host ("Single head OK: " + (($headIds -join ' ') -replace '^\s*$','(none reported)'))
}

# Prefer flask db upgrade if CLI is present
$flaskHelp = docker compose run --rm web flask --help 2>$null
if($flaskHelp -match '(?i)\bdb\b'){
  docker compose run --rm web bash -lc 'export FLASK_APP=erp:create_app; flask db upgrade || alembic upgrade head'
} else {
  docker compose run --rm web alembic upgrade head
}

docker compose up -d
docker compose logs --tail=200 -f web

