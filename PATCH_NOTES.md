
# Phase 1 (Critical) Patch — 2025-10-19

This patch introduces *production-critical* foundations:
- Security headers (CSP, HSTS, Referrer-Policy, X-Frame-Options, etc.)
- Minimal, dependency-free RBAC decorator
- Centralized JSON error handlers with correlation IDs
- Request ID + structured logging bootstrap
- Environment-first configuration loader with basic validation
- App factory wires all of the above
- Non-blocking CI skeleton (separate workflow file) to start linting & tests

## How to apply

1) **Unzip into your repo root** (same folder that has `erp/`, `tests/`, etc.).
   - On Windows PowerShell:
     ```powershell
     Expand-Archive -Path .\phase1_critical_patch.zip -DestinationPath . -Force
     ```

2) **Commit**:
   ```powershell
   git add -A
   git commit -m "phase1-critical: security headers, RBAC decorator, error handlers, observability, config; CI skeleton"
   git push origin main
   ```

> Safe-by-default: No new third‑party dependencies are introduced in this patch.

## New files

- `erp/security.py` — sets strict security headers via `after_request`
- `erp/authz.py` — `require_permissions` decorator (RBAC) using existing `erp.utils.has_permission`
- `erp/errors.py` — JSON error responses (400/401/403/404/500) with `request_id`
- `erp/observability.py` — request ID, structured logging, optional Sentry init
- `erp/config.py` — environment-driven config + validation hook
- `.github/workflows/phase1-ci.yml` — non-blocking starter CI (ruff, mypy (soft), pytest (soft), gitleaks if present)
- `docs/PHASE1_CHANGELOG.md` — traceability for this batch

## Post-merge checklist

- Set `FLASK_ENV=production` in your runtime env (or equivalent) and ensure `DATABASE_URL` points to your DB
- If you have a Sentry DSN, set `SENTRY_DSN` to enable error reporting automatically
- Wire RBAC onto sensitive routes, e.g.:
  ```python
  from erp.authz import require_permissions

  @bp.route("/admin/tenants", methods=["POST"])
  @require_permissions({"tenant:create"})
  def create_tenant():
      ...
  ```

## Rollback

All changes are additive or narrow edits to `erp/__init__.py`. You can revert the commit:
```powershell
git revert <commit-sha>
```
