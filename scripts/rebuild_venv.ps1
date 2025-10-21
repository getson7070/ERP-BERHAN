Param()
$ErrorActionPreference = 'Stop'
$py = & { 
  if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } 
  elseif (Test-Path 'C:\Program Files\Python311\python.exe') { 'C:\Program Files\Python311\python.exe' } 
  else { 'python' } 
}
Write-Host "Using Python: $py"

# Clean venv
if (Test-Path .\.venv) { Remove-Item .\.venv -Recurse -Force }

& $py -m venv .venv
& .\.venv\Scripts\python.exe -m ensurepip --upgrade
& .\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c constraints.txt
