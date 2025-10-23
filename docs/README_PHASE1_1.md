# Phase 1.1 — Security autopilot (additive, non-destructive)

This patch adds:
- `.github/workflows/pip-audit.yml` — runs pip-audit on PRs/pushes (non-blocking for now).
- `.github/workflows/dependabot-auto-merge.yml` — auto-merges Dependabot SECURITY patch/minor PRs once checks are green.
  - Uses `dependabot/fetch-metadata` to gate by type/severity.
  - Attempts auto-approval with `GITHUB_TOKEN` (works in some repos; if required reviews remain, a maintainer's approval still needed).
  - You can later add a fine-grained PAT as a secret (e.g., `AUTO_MERGE_PAT`) and swap the approval step to a user-backed approval.

## After merge — Recommended
1) Keep the three Phase-1 checks as **required** on `main`.
2) Add preview check as **required** after it’s stable.
3) If you want pip-audit to be blocking, set `continue-on-error: false` and add its check name to branch protection.

No migrations created, no schema changes.
