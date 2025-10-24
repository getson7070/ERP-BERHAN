param([Parameter(Mandatory=$true)][string]$RepoPath)
$ErrorActionPreference = "Stop"
$targets = @("erp\app.py","erp\__init__.py")
$inserted=$false
foreach ($t in $targets) {
  $path = Join-Path $RepoPath $t
  if (!(Test-Path $path)) { continue }
  $c = Get-Content $path -Raw
  if ($c -match "from\s+erp\.auth\.mfa_routes\s+import\s+bp\s+as\s+mfa_bp") {
    Write-Host "[mfa-wire] already wired in $t"; $inserted=$true; break
  }
  $imp = "from erp.auth.mfa_routes import bp as mfa_bp"
  $reg = "app.register_blueprint(mfa_bp)"
  if ($c -match "def\s+create_app\(") {
    $c = $imp + "`n" + $c
    $c = $c -replace "(def\s+create_app\([^\)]*\):\s*\n\s*[^#\n]*\n)","$0    $reg`n"
    Set-Content -Path $path -Value $c -Encoding UTF8
    Write-Host "[mfa-wire] wired into $t"
    $inserted=$true; break
  }
}
if (-not $inserted) { Write-Warning "[mfa-wire] could not wire MFA automatically. Please register mfa_bp manually." }
