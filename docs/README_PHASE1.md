# Phase 1 (Critical) Additive Patch

This patch is **additive** and **non-destructive**:
- Adds CI gates for **single Alembic head**, **secret scanning**, and **env-contract parity**.
- Includes `.env.example.phase1` so it **will not overwrite** any existing `.env.example`.
- No database schema changes. No migrations are created.

## New workflow gates
- `.github/workflows/alembic-single-head.yml`: blocks merges if more than one Alembic head exists.
- `.github/workflows/gitleaks.yml`: scans for secrets in PRs/commits.
- `.github/workflows/env-contract.yml`: ensures example env files list all required keys.

## Scripts
- `scripts/check_alembic_single_head.py`: thin wrapper over `alembic heads -q` to detect multiple heads.
- `scripts/check_env_contract.py`: validates `docs/env.contract.json` requirements against example env files.

## Env Contract
- `docs/env.contract.json`: source-of-truth for required env keys. Expand as needed.
- `.env.example.phase1`: safe template that won't clobber your existing `.env.example`.

## After merge (recommended settings)
1. Enable **branch protection** on `main` and mark the above workflows as **required**.
2. Keep **preview** (Netlify/App Runner) as a required check once configured.
3. Run `alembic heads` locally; if >1, create a merge revision and re-run.
