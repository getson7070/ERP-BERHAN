
<#
Idempotently injects Phase1 bootstrap call into erp\__init__.py.
- Finds the first 'def create_app' block and replaces the first 'return app' inside it
  with a snippet that calls apply_phase1_hardening(app) before returning.
- If patterns not found, prints manual instructions and exits 0 without changes.
#>

param(
    [string]$FilePath = "$(Resolve-Path -LiteralPath 'erp\__init__.py' -ErrorAction SilentlyContinue)"
)

if (-not $FilePath -or -not (Test-Path $FilePath)) {
    Write-Host "[phase1] __init__.py not found. Skipping automatic wiring."
    Write-Host "Manual step: Add the following just before 'return app' inside create_app(...):"
    Write-Host "    try:`n        from erp.bootstrap_phase1 import apply_phase1_hardening`n        apply_phase1_hardening(app)`n    except Exception as e:`n        app.logger.warning(f\"Phase1 bootstrap skipped: {{e}}\")"
    exit 0
}

$content = Get-Content -LiteralPath $FilePath -Raw

# Avoid duplicate insertion
if ($content -match "apply_phase1_hardening\\(app\\)") {
    Write-Host "[phase1] Bootstrap already wired. No changes."
    exit 0
}

# Roughly locate create_app block and the first 'return app' within it
$pattern = "(?s)(def\\s+create_app\\s*\\(.*?\\)\\s*:\\s*)(.*?)(\\breturn\\s+app\\b)"
$replSnippet = @"
try:
        from erp.bootstrap_phase1 import apply_phase1_hardening
        apply_phase1_hardening(app)
    except Exception as e:
        app.logger.warning(f"Phase1 bootstrap skipped: {e}")
    return app
"@

$new = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, { param($m)
    $m.Groups[1].Value + $m.Groups[2].Value + $replSnippet
}, 1)

if ($new -ne $content) {
    Copy-Item -LiteralPath $FilePath -Destination "$FilePath.bak_phase1" -Force
    Set-Content -LiteralPath $FilePath -Value $new -NoNewline
    Write-Host "[phase1] Wired bootstrap into create_app(). Backup at $FilePath.bak_phase1"
    exit 0
} else {
    Write-Host "[phase1] Could not safely identify 'return app' inside create_app()."
    Write-Host "Manual step: Add the following just before 'return app' inside create_app(...):"
    Write-Host "    try:`n        from erp.bootstrap_phase1 import apply_phase1_hardening`n        apply_phase1_hardening(app)`n    except Exception as e:`n        app.logger.warning(f\"Phase1 bootstrap skipped: {{e}}\")"
    exit 0
}
