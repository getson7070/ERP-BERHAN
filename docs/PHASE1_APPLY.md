# Phase 1 Apply Guide (Very Critical)

## 1) Backup and branch (optional)
```powershell
git checkout -b phase1_2025_10_24
```

## 2) Overlay the patch
Unzip the archive at the repository root so that files land in the same relative paths. This patch **replaces** the following files if present and **adds** the rest:
- `db.py`
- `erp/__init__.py`
- `erp/extensions.py`
- `migrations/env.py`
- `gunicorn.conf.py`
- `wsgi_eventlet.py`
- `scripts/run_migrations.sh`
- `scripts/rotate_jwt_secret.py`
- `.env.example` (lines appended if already present)

## 3) Environment
Set minimally (Render → Environment):
```bash
SECRET_KEY=<32+ random chars>
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname
RATELIMIT_STORAGE_URI=redis://<host>:6379/0
REDIS_URL=redis://<host>:6379/0
PROMETHEUS_MULTIPROC_DIR=/tmp/prom
WEB_CONCURRENCY=2
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=60
```

## 4) Install & migrate
```bash
pip install -r requirements.txt
bash scripts/run_migrations.sh
```

## 5) Run (local)
```bash
export FLASK_ENV=production
gunicorn -c gunicorn.conf.py wsgi:app
```

## 6) Render notes
- Health check path: `/healthz` (served by routes/health.py or default handler)
- Pre-deploy command: `bash scripts/run_migrations.sh`
- Start command: `gunicorn -c gunicorn.conf.py wsgi:app` (or `wsgi_eventlet:app`)

## Rollback
Use `git restore` to revert any single file if needed.
