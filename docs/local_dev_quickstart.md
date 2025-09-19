# Local Development Quickstart

This quickstart bootstraps a secure ERP-BERHAN dev environment that mirrors production controls.

## Prerequisites
- Python 3.11–3.13 (CPython, tested)
  - **Windows:** install the 64-bit Python 3.11.x release from [python.org](https://www.python.org/downloads/windows/), enable *Add python.exe to PATH* and *Install launcher for all users*. Verify with `py -3.11 --version` before continuing.
- Docker (for PostgreSQL and Redis) or a PostgreSQL 16 instance you manage
- Git and GPG configured for signed commits

## Setup Steps
1. **Clone and create a virtualenv**
   ```bash
   git clone https://github.com/getson7070/ERP-BERHAN.git
   cd ERP-BERHAN
   python -m venv .venv                # macOS/Linux
   source .venv/bin/activate
   ```
   ```powershell
   py -3.11 -m venv .venv              # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```
2. **Install locked dependencies**
   ```bash
   pip install -r requirements.lock
   ```
3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # edit values as needed (DB URL, secrets, mail settings)
   ```
4. **Start services**
   ```bash
   docker compose up -d db redis
   ```
   - If Docker Desktop is unavailable, point the app and Alembic at an existing PostgreSQL instance by setting `DATABASE_URL` (and `ALEMBIC_URL` if different) before running migrations. SQLite is also supported for lightweight smoke tests: `export DATABASE_URL=sqlite:///$(pwd)/instance/erp_dev.db` (PowerShell: `$Env:DATABASE_URL = "sqlite:///$(Resolve-Path .\instance\erp_dev.db)"`).
5. **Run database migrations and seed an admin**
   ```bash
   scripts/run_migrations.sh
   ADMIN_USERNAME=admin ADMIN_PASSWORD=strongpass python init_db.py
   ```
   The migration helper now respects `ALEMBIC_URL`/`DATABASE_URL`, so Windows users can run `alembic -x url=$Env:DATABASE_URL upgrade head` when working without Docker.
6. **Launch the app, worker, and beat**
   ```bash
   flask run
   celery -A erp.celery worker --loglevel=info
   celery -A erp.celery beat --loglevel=info
   ```
7. **Smoke test**
   ```bash
   curl -f http://localhost:5000/health
   pytest tests/smoke
   ```
8. **Run accessibility checks**
   ```bash
   ./scripts/run_pa11y.sh http://localhost:5000
   ```

For a guided tour with sample data, see [docs/guided_setup.md](guided_setup.md).

## Windows Troubleshooting Checklist

- `py` or `py -3.11` not found: reinstall Python 3.11.x with the *Install launcher* option selected, then reopen PowerShell.
- `alembic upgrade head` fails with `Connection refused`: ensure PostgreSQL is running (e.g., `docker compose up -d db`) or export `DATABASE_URL` to a reachable instance and rerun `scripts/run_migrations.sh`.
- `RuntimeError: FLASK_SECRET_KEY/SECRET_KEY not set`: copy `.env.example` to `.env` and populate `FLASK_SECRET_KEY`, `SECURITY_PASSWORD_SALT`, and `JWT_SECRET` (use `python -c "import secrets; print(secrets.token_urlsafe(32))"`). Reload the shell so the variables are available before launching Flask.
