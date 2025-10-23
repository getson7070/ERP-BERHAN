# Phase 1 Checklist (ERP-BERHAN)
- [ ] CODEOWNERS at `.github/CODEOWNERS` with correct owners
- [ ] `security-gates.yml` passing and **blocking**
- [ ] `migrations-dry-run.yml` passing (single alembic head, upgrade ok)
- [ ] `build-sign-and-verify.yml` passing; artifact signed & verified
- [ ] `post-deploy-smoke.yml` wired with `SMOKE_*` secrets; passes or blocks
- [ ] `rbac-policy-check.yml` passing with real `policy/rbac.yml`
- [ ] Branch protection enabled per `docs/branch_protection_gh_cli.md`
- [ ] Secrets set: `SMOKE_ADMIN_USER`, `SMOKE_ADMIN_PASS`
