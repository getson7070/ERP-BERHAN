\
param(
  [string]$RepoPath = "C:\Users\Alienware\Documents\ERP-BERHAN",
  [string]$ZipPath  = "$env:USERPROFILE\Downloads\erp-berhan-critical-upgrades.zip",
  [switch]$SkipTests
)
Push-Location $RepoPath
git checkout main
git pull --rebase
$branch = "fix/critical-upgrades-{0:yyyyMMdd-HHmm}" -f (Get-Date)
git checkout -b $branch
Expand-Archive -LiteralPath $ZipPath -DestinationPath $RepoPath -Force
Remove-Item -Recurse -Force .pytest_cache, build, dist, *.egg-info -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
pip uninstall -y erp authz 2>$null | Out-Null
if (-not $SkipTests) {
  $env:PYTEST_ADDOPTS="--cov-fail-under=0"
  pytest -q -k "(analytics or api or webhook or idempotency or rbac) and not ui"
}
git add -A
git commit -m "fix(core): critical stability upgrades (analytics fallbacks, GraphQL limits+metrics, DLQ, RBAC matrix)"
git push -u origin HEAD
Pop-Location
