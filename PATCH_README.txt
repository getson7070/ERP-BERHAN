ERP-BERHAN 10/10 Inventory-First Patch — 2025-10-15 08:42:15

WHAT THIS PATCH DOES
--------------------
1) Fixes CSRF + session secret usage (Flask-WTF & SECRET_KEY).
2) Ensures login works with a proper LoginForm and templates.
3) Adds starter Inventory / Orders / Marketing modules and pages.
4) Fixes Eventlet warnings by monkey-patching early in wsgi.py.
5) Fixes static logo path with a graceful fallback if the file is missing.
6) Bypasses broken Alembic migrations by pointing Alembic to a *clean* versions dir:
   - migrations/versions_clean contains a single initial revision (0001_initial_core.py).
   - scripts/migrations/automerge_and_upgrade.py now only upgrades to head using the clean chain.
   - Your old, conflicting versions are ignored (they remain on disk, but are not used).

HOW TO APPLY
------------
1) Extract this zip into your repo root (the folder that contains 'migrations' and 'erp').
2) Commit the changes.
3) Ensure DATABASE_URL is set in Render (or SQLALCHEMY_DATABASE_URI).
4) Deploy. The pre-deploy will run 'python -m scripts.migrations.automerge_and_upgrade' which upgrades to the clean head.

NOTES
-----
- This patch focuses on Inventory/Orders/Marketing over Finance, per your request.
- Extend the clean migration chain with further revisions in 'migrations/versions_clean' (not the old 'versions' dir).
- If you also want to *remove* the broken migrations, delete 'migrations/versions/*' in your repo permanently.
- Default credentials are NOT seeded. Create a user via shell or add a seeding revision in versions_clean.

TROUBLESHOOTING PATCH APPLICATION
---------------------------------
- Ensure your working tree is clean before running this script (`git status` should show no pending changes). Stash or commit
  any local edits to avoid conflicts.
- If you have previously applied a `codex-fix-tests*.patch` file or re-run this script, check whether the changes already
  exist. Reapplying identical hunks will fail; use `git apply --check <patch>` to confirm whether a patch still applies.
- If the patch is outdated relative to your branch, refresh it from the latest `main` or rebase your branch so file offsets
  match.
- Only one automation or user should apply patches at a time. Concurrent runs that touch the same files can cause the
  "Failed to apply patch" error seen in CI.
