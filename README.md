    # ERP-BERHAN — Clean Build (Final Patch)

    This patch ensures:
    - Single Alembic chain: `8de54ef00fde` (bridge baseline) → `0001_initial_core` (head)
    - Robust Alembic config that prefers `DATABASE_URL` (with postgres scheme fix)
    - Safer deployment defaults for SQLite local and Postgres on Render
    - Line ending enforcement (LF) to avoid Linux runtime issues
    - Minimal UI route and template to verify the app is up

    ---

    ## Local dev (SQLite)

    ```bash
    python -m venv .venv
    . .venv/bin/activate  # Windows Git Bash: source .venv/Scripts/activate
    pip install -r requirements.txt
    ```

    Start fresh:

    ```bash
    export DATABASE_URL="sqlite:///dev.db"
    # remove version row then upgrade to head
    alembic -c alembic.ini stamp 8de54ef00fde
    alembic -c alembic.ini upgrade head

    # run the app:
    export FLASK_APP="wsgi.py"
    flask run
    ```

    ## Postgres (Render)

    Use the exact `DATABASE_URL` from your Render service, **no placeholders**. If the URL starts with
    `postgres://`, we normalize it to `postgresql+psycopg2://` automatically.

    ```bash
    # Example only — replace with your actual values from Render
    export DATABASE_URL="postgresql+psycopg2://USER:P%40SS%3Aw0RD@HOST:5432/DBNAME?sslmode=require"

    # Optional: URL-encode a password
    # export PASSWORD_ENC="$(python - <<'PY'
import urllib.parse, os;print(urllib.parse.quote(os.environ['PASSWORD']))
PY)"
    ```

    Once `DATABASE_URL` is correct:

    ```bash
    alembic -c alembic.ini stamp 8de54ef00fde
    alembic -c alembic.ini upgrade head
    ```

    ## Migration graph sanity check (no DB needed)

    ```bash
    python - <<'PY'
    from alembic.config import Config
    from alembic.script import ScriptDirectory as S; s=S.from_config(Config('alembic.ini'))
    print('BASES:', [h.revision for h in s.get_bases()])
    print('HEADS:', [h.revision for h in s.get_heads()])
    PY
    # Expected:
    # BASES: ['8de54ef00fde']
    # HEADS: ['0001_initial_core']
    ```

    ## Render deployment

    - Build command: `pip install -r requirements.txt`
    - Start command (gunicorn): `gunicorn wsgi:app --workers 2 --threads 4 --timeout 120`
    - Required env vars:
        - `DATABASE_URL` (Render Postgres supplies it)
        - `SECRET_KEY` (set any strong random value)
        - Optional: `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=5`
