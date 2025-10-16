# ERP-BERHAN — Clean Build (Final Patch)

This patch ensures:
- Single Alembic chain: `8de54ef00dfe` (bridge baseline) → `0001_initial_core` (head)
- Robust Alembic config that prefers `DATABASE_URL` (with postgres scheme fix)
- Safer deployment defaults for SQLite local and Postgres on Render
- Line ending enforcement (LF) to avoid Linux runtime issues
- Minimal UI route and template to verify the app is up

## Local dev (SQLite)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# start fresh
Remove-Item .\dev.db -ErrorAction SilentlyContinue
$env:DATABASE_URL = "sqlite:///dev.db"

# seed version row then upgrade to head
alembic -c alembic.ini stamp 8de54ef00dfe
alembic -c alembic.ini upgrade head

# run the app
$env:FLASK_APP="wsgi.py"
flask run
```

## Postgres (Render)

Use the exact `DATABASE_URL` from your Render service, **no placeholders**.
If the URL starts with `postgres://`, we will normalize it to
`postgresql+psycopg2://` automatically.

```powershell
# Example only — replace with your actual values from Render
$env:DATABASE_URL = "postgresql+psycopg2://USER:P%40SS%3AWORD@HOST:5432/DBNAME?sslmode=require"

# Optional: URL-encode a password
# $encoded = [System.Uri]::EscapeDataString("<PASSWORD>")
# $env:DATABASE_URL = "postgresql+psycopg2://USER:$encoded@HOST:5432/DBNAME?sslmode=require"

# Once DATABASE_URL is correct:
alembic -c alembic.ini stamp 8de54ef00dfe
alembic -c alembic.ini upgrade head
```

## Migration graph sanity check (no DB needed)

```powershell
python -c "from alembic.config import Config; from alembic.script import ScriptDirectory as S; s=S.from_config(Config('alembic.ini')); print('BASES:', s.get_bases()); print('HEADS:', s.get_heads())"
# Expected:
# BASES: ['8de54ef00dfe']
# HEADS: ['0001_initial_core']
```

## Render deployment

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn wsgi:app --workers 2 --threads 4 --timeout 120`
- Required env vars:
    - `DATABASE_URL` (Render Postgres supplies it)
    - `SECRET_KEY` (set any strong random value)
    - Optional: `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=5`
