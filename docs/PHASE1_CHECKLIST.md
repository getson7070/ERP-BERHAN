# Phase-1 Checklist (Blocking Gates)

**Goal:** Reach ~9.3–9.4/10 score and ~93–95% production readiness without touching runtime behavior.

## What this overlay adds
- `.github/CODEOWNERS` with required reviewers for critical paths.
- CI gates:
  - Secret scanning (gitleaks)
  - GitHub Dependency Review
  - `pip-audit` for Python vulnerabilities
  - Alembic upgrade→head and downgrade→base dry-run on an ephemeral DB
- Post-deploy `smoke` workflow (manual trigger) that checks `/healthz`, `/api/ping`, `/auth/login` against a URL you provide.
- `policy/rbac.yml` template + CI lint to prevent policy drift (fails if missing/invalid).

## What it does **not** do
- No changes to app runtime code.
- No changes to Render/AppRunner configs.
- No secrets added to repo.

## After merging this overlay
1. In GitHub Settings → Branches → `main`, enable:
   - Require pull request reviews (set desired number).
   - Require status checks to pass: select **Phase-1 CI Gates**, **RBAC Policy Lint**.
   - Disallow force pushes & deletions.
2. Add repository secret(s) later for deploy automation if desired (Phase-2).
3. Run the **Post-Deploy Smoke** workflow with your app URL after deployment.

If any gate fails, fix the problem or adjust policy intentionally—don’t suppress the gate.
