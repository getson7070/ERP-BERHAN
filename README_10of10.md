# ERP-BERHAN "10/10" Upgrade Patch

This pack stabilizes production deployment (Render), fixes auth/CSRF/session,
hardens migrations, and sets a clean foundation for cross-module integration.

## What's Included
1. **Migrations**
   - `scripts/migrations/automerge_and_upgrade.py` — robust v3 automerge: de-dupes duplicate revision IDs across nested folders, computes true heads from files, merges *only* heads (with pairwise fallback), then upgrades to head.
   - Optional `scripts/migrations/squash.py` — tool to squash all history into a single base once you're stable.

2. **App Factory / Extensions / Security**
   - `erp/extensions.py` — single source of truth for SQLAlchemy, Migrate, CSRF, LoginManager, Limiter, Cache, Mail, SocketIO.
   - `erp/__init__.py` — `create_app()` with production config, CSRF, session, Login, CORS, Limiter storage, Cache.
   - `erp/context.py` — template context processors (ensures `csrf_token` in Jinja when needed).
   - `erp/security/policies.py` — `role_required` decorator and `device_authorized` helper stub.
   - `erp/routes/__init__.py` — safe blueprint auto-register (will import & register if modules exist; otherwise skips).

3. **WSGI / Gunicorn**
   - `wsgi.py` — **eventlet.monkey_patch()** before anything else.
   - `gunicorn.conf.py` — eventlet worker; health timeouts appropriate for Render.

4. **Templates (login example)**
   - `erp/templates/auth/login.html` — reference login with CSRF and `url_for('static', ...)` usage.

5. **Static**
   - Placeholder `erp/static/pictures/BERHAN PHARMA LOGO.jpg` (empty sentinel). Replace with your real file (exact name).

6. **Preflight**
   - `scripts/preflight.py` — quick checks for SECRET_KEY, DATABASE_URL, static asset, blueprint import, etc.

7. **Config**
   - `config.py` — production defaults; read env vars used by Render.

## How to Apply
1. **Back up** your repo and DB.
2. Copy these files into your project **preserving paths**.
3. Ensure your project package is named **`erp`** (or adjust imports in these files).
4. Set Render **Environment Variables**:
   - `SECRET_KEY` (strong random; do **not** rotate between deploys)
   - `DATABASE_URL` (Postgres URI)
   - `RATELIMIT_STORAGE_URI` (`redis://...` if using Flask-Limiter in prod; or omit to use memory:// for dev)
   - `FLASK_ENV=production` (optional)
5. Keep your pre-deploy command:
   ```bash
   python -m scripts.migrations.automerge_and_upgrade
   ```
6. Gunicorn start (Render) example:
   ```bash
   gunicorn "wsgi:app" --config gunicorn.conf.py
   ```

## Optional: Full Squash (after you are stable)
If you want a *single* clean migration history:
```bash
python -m scripts.migrations.squash --confirm
```
This will create a new base migration with your current metadata. **Use only when the live DB matches your models.**

## Notes
- The blueprint auto-register will not break if a module is absent; it prints a warning and continues.
- The login example assumes a `User` model with `id` primary key; adjust if different.
- Replace the placeholder logo with your real file.
