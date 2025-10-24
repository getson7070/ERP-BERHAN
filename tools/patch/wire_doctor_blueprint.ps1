param([Parameter(Mandatory=$true)][string]$RepoPath)
$ErrorActionPreference = "Stop"
$targets = @("erp\app.py","erp\__init__.py")
$inserted=$false
foreach ($t in $targets) {
  $path = Join-Path $RepoPath $t
  if (!(Test-Path $path)) { continue }
  $c = Get-Content $path -Raw
  if ($c -match "from\s+erp\.ops\.doctor\s+import\s+bp\s+as\s+doctor_bp") {
    Write-Host "[doctor-wire] already wired in $t"; $inserted=$true; break
  }
  $imp = "from erp.ops.doctor import bp as doctor_bp"
  $reg = "app.register_blueprint(doctor_bp)"
  if ($c -match "def\s+create_app\(") {
    $c = $imp + "`n" + $c
    $c = $c -replace "(def\s+create_app\([^\)]*\):\s*\n\s*[^#\n]*\n)","$0    $reg`n"
    Set-Content -Path $path -Value $c -Encoding UTF8
    Write-Host "[doctor-wire] wired into $t"
    $inserted=$true; break
  }
}
if (-not $inserted) { Write-Warning "[doctor-wire] could not wire Doctor automatically. Please register doctor_bp manually." }
