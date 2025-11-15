param([string]$Repo = "$(Split-Path -Parent $PSCommandPath)\..\..")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# 1) venv
Set-Location $Repo
if (-not (Test-Path "$Repo\.venv\Scripts\Activate.ps1")) { python -m venv "$Repo\.venv" }
. "$Repo\.venv\Scripts\Activate.ps1"

# 2) Load .env.dev.local safely using Env: provider (works with dynamic keys)
function Import-DotEnv {
  param([string]$Path = ".env.dev.local")
  if (-not (Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*$') { return }
    $kv = $_.Split('=', 2)
    if ($kv.Count -eq 2) {
      $k = $kv[0].Trim()
      $v = $kv[1].Trim()
      if (-not (Test-Path ("Env:{0}" -f $k))) {
        Set-Item -Path ("Env:{0}" -f $k) -Value $v
      }
    }
  }
}
Import-DotEnv "$Repo\.env.dev.local"

# 3) Backfill defaults (only if still missing)
if (-not (Test-Path Env:SECRET_KEY))     { Set-Item Env:SECRET_KEY     ([guid]::NewGuid().ToString("N")) }
if (-not (Test-Path Env:JWT_SECRET_KEY)) { Set-Item Env:JWT_SECRET_KEY ([guid]::NewGuid().ToString("N")) }
if (-not (Test-Path Env:DATABASE_URL))   {
  $DevDb = Join-Path $Repo "dev.sqlite3"
  Set-Item Env:DATABASE_URL ("sqlite:///" + ($DevDb -replace "\\", "/"))
}
if (-not (Test-Path Env:PYTHONPATH))     { Set-Item Env:PYTHONPATH $Repo }
if (-not (Test-Path Env:STRICT_CONFIG))  { Set-Item Env:STRICT_CONFIG "0" }

# Flask defaults
Set-Item Env:FLASK_APP "erp:create_app"
if (-not (Test-Path Env:FLASK_ENV)) { Set-Item Env:FLASK_ENV "development" }

# Done
Write-Host "Dev env ready. PWD=$PWD PYTHONPATH=$env:PYTHONPATH DB=$env:DATABASE_URL"
