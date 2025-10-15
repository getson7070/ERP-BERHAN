ERP-BERHAN 10/10 Patch v3
=========================

This patch focuses on three areas:
1) **Migrations**: make the Alembic tree linear and stable (no auto-merging during deploy).
2) **Flask app hardening**: CSRF enabled, stable SECRET_KEY handling, session + Flash working, Socket.IO WSGI sanity.
3) **Static + templates**: fix logo path and provide csrf_token in templates that don't use FlaskForm.

---

APPLYING THE PATCH
------------------
1. Unzip this patch at the root of your repo (where `ERP-BERHAN-main/` lives). Allow files to overwrite.

2. Delete placeholder migrations that have `revision=None` from your repo (we list a helper script below).
   Then **commit** the merge revision included here which merges your two current heads:
   - 20251014_merge_heads_for_77
   - 20251014_merge_heads_stable

   After commit, your migration tree MUST have exactly 1 head.

3. **Stop auto-merging in deploy**: update `render.yaml` (provided) so preDeploy only runs `alembic upgrade head`.
   The included `scripts/predeploy.sh` aborts the deploy if your repo still has multiple heads.

4. Ensure these environment variables are defined on Render:
   - SECRET_KEY  (a long, random, stable value — do **not** rotate unless you want to invalidate all sessions)
   - DATABASE_URL
   - REDIS_URL   (optional but recommended, for Socket.IO and Flask-Limiter; or switch to in-memory for dev)
   - FLASK_ENV=production

5. Deploy. If predeploy aborts with "multiple heads", run locally:
   ```bash
   python tools/linearize_migrations.py --report
   # if heads>1 and all clean:
   # git add migrations/versions/20251015_merge_heads_final.py
   # git commit -m "Merge Alembic heads into single linear chain"
   ```

WHY PRE-DEPLOY WAS FAILING
--------------------------
- Your repo currently has **two heads** and **placeholder migration files with `revision=None`**. The script
  `scripts/migrations/automerge_and_upgrade.py` tried to create new merge revisions **during deploy**.
  Alembic refused because some of the names you pass are not heads (`...seed_test_users_dev`) and there are
  **duplicate revision IDs present more than once**. Deploy-time auto-merging is brittle and writes files that
  are not committed, diverging the graph between builds. We remove that behavior.

- `csrf_token is undefined` and `The session is unavailable because no secret key was set` came from missing
  `CSRFProtect` and a **missing SECRET_KEY**. This patch enables CSRF and uses a stable SECRET_KEY from env.
  Without a stable SECRET_KEY, Flask cannot sign session cookies and **authorized devices are forgotten**.

- The logo path referenced a filename with spaces (`BERHAN PHARMA LOGO.jpg`) that does not exist on disk;
  we standardize it to `BERHAN-PHARMA-LOGO.jpg`. Replace with your real asset under `static/pictures/`.

WHAT THIS PATCH CHANGES
-----------------------
- Adds `tools/linearize_migrations.py` — a safe checker/fixer for Alembic heads (no changes during deploy).
- Adds a **manual merge** revision `migrations/versions/20251015_merge_heads_final.py` (edit if dates/IDs differ).
- Replaces `scripts/migrations/automerge_and_upgrade.py` with a non-destructive checker.
- Adds `scripts/predeploy.sh` used by `render.yaml`.
- Hardens Flask app:
  - Initializes CSRFProtect and injects `csrf_token()` into Jinja for non-FlaskForm pages.
  - Ensures SECRET_KEY comes from env with a clear error on missing in production.
  - Fixes `wsgi.py` to early monkey-patch eventlet (if you use it).
- Updates base template to load the logo at `static/pictures/BERHAN-PHARMA-LOGO.jpg`.

After applying and committing these changes, run locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=ERP-BERHAN-main
export FLASK_ENV=development
export SECRET_KEY="$(python - <<'PY'
import secrets; print(secrets.token_hex(32))
PY)"
alembic upgrade head
flask run
```

Then deploy to Render.
