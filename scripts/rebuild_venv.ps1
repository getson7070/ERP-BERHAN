param(
    [string] $RepoPath = (Get-Location).Path
)

$venv = Join-Path $RepoPath ".venv"
if (Test-Path $venv) {
    Write-Host "Removing existing venv at $venv"
    Remove-Item -Recurse -Force $venv
}

$python = (Get-Command python -ErrorAction SilentlyContinue).Path
if (-not $python) { throw "python not found on PATH" }
Write-Host "Using Python: $python"

& $python -m venv $venv

$activate = Join-Path $venv "Scripts\Activate.ps1"
. $activate

python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

$req = Join-Path $RepoPath "requirements-dev.txt"
$cons = Join-Path $RepoPath "constraints.txt"
python -m pip install -r $req -c $cons
