# Local Development Quickstart

This guide bootstraps a secure ERP-BERHAN environment that mirrors production controls while documenting platform-specific caveats observed by contributors.

## Prerequisites
- Python 3.11–3.13 (CPython, tested)
  - **Windows:** install the 64-bit Python 3.11.x release from [python.org](https://www.python.org/downloads/windows/), enable *Add python.exe to PATH* and *Install launcher for all users*, then verify with `py -3.11 --version`.
- Virtual environment tooling (`python -m venv` ships with CPython)
- Docker (for PostgreSQL and Redis) or a PostgreSQL 16 instance you manage
- Git and GPG configured for signed commits

> **Why 3.11?** The lockfile targets CPython 3.11–3.13, but Python 3.13 on Windows frequently attempts to compile native wheels (e.g., `greenlet`) when the launcher is missing. Installing 3.11 with the launcher avoids this pitfall.

## Standard workflow (macOS/Linux)
1. **Clone and create a virtual environment**
   ```bash
   git clone https://github.com/getson7070/ERP-BERHAN.git
   cd ERP-BERHAN
   python3 -m venv .venv
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
3. **Copy the environment template and generate secrets**
   ```bash
   cp .env.example .env
   python scripts/generate_secret_keys.py --bytes 48
   python -c "import secrets; print(secrets.token_urlsafe(48))"  # JWT_SECRET
   ```
   The helper script prints `FLASK_SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, and `SECURITY_PASSWORD_SALT` in `KEY=value` format—append
   each line to `.env` or export them with your preferred shell tooling.
4. **Start PostgreSQL + Redis**
   ```bash
   docker compose up -d db redis
   ```
   - If Docker Desktop is unavailable, point the app and Alembic at an existing PostgreSQL instance by setting `DATABASE_URL` (and `ALEMBIC_DATABASE_URL` if different) before running migrations. SQLite is also supported for lightweight smoke tests: `export DATABASE_URL=sqlite:///$(pwd)/instance/erp_dev.db` (PowerShell: `$Env:DATABASE_URL = "sqlite:///$(Resolve-Path .\instance\erp_dev.db)"`).
5. **Run migrations and optional seed data**
   ```bash
   alembic upgrade head
   ADMIN_USERNAME=admin ADMIN_PASSWORD=StrongPass1! SEED_DEMO_DATA=1 python init_db.py
   ```
   The migration helper now respects `ALEMBIC_DATABASE_URL`/`DATABASE_URL`, so Windows users can run `alembic -x url=$Env:DATABASE_URL upgrade head` when working without Docker.
6. **Launch the services**
   ```bash
   flask run --port 8080
   celery -A erp.celery worker --loglevel=info
   celery -A erp.celery beat --loglevel=info
   ```
7. **Smoke test**
   ```bash
   curl -f http://localhost:8080/healthz
   pytest tests/smoke
   ```

## Windows 11 / PowerShell walkthrough
The following commands assume PowerShell 7+, but they also work in Windows PowerShell once execution policy allows scripts in the current session (`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`).

1. **Remove any previous clone**
   ```powershell
   if (Test-Path "$HOME\Documents\ERP-BERHAN") { Remove-Item "$HOME\Documents\ERP-BERHAN" -Recurse -Force }
   git clone https://github.com/getson7070/ERP-BERHAN.git
   cd ERP-BERHAN
   ```
   > If you see `fatal: destination path 'ERP-BERHAN' already exists`, delete (or rename) the existing directory before cloning.

2. **Install Python 3.11 with the launcher**
   ```powershell
   $Url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
   $Installer = "$env:TEMP\python311.exe"
   Invoke-WebRequest -Uri $Url -OutFile $Installer
   Start-Process -FilePath $Installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_launcher=1 Include_pip=1" -Wait
   ```
   Verify the launcher is present:
   ```powershell
   py --version  # should report Python 3.11.x
   ```
   If `py` is still not recognised, ensure *Python Launcher for Windows* is selected in **Add/Remove Programs → Python 3.11 → Modify**.

3. **Create and activate the virtual environment**
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.lock
   ```

4. **Generate secrets and copy the template**
   ```powershell
   Copy-Item .env.example .env -Force
   python .\scripts\generate_secret_keys.py --bytes 48
   $Env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
   $Env:WTF_CSRF_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
   $Env:SECURITY_PASSWORD_SALT = python -c "import secrets; print(secrets.token_urlsafe(32))"
   $Env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
   [System.Environment]::SetEnvironmentVariable("FLASK_SECRET_KEY", $Env:FLASK_SECRET_KEY)
   [System.Environment]::SetEnvironmentVariable("WTF_CSRF_SECRET_KEY", $Env:WTF_CSRF_SECRET_KEY)
   [System.Environment]::SetEnvironmentVariable("SECURITY_PASSWORD_SALT", $Env:SECURITY_PASSWORD_SALT)
   [System.Environment]::SetEnvironmentVariable("JWT_SECRET", $Env:JWT_SECRET)
   ```
   > These environment variables are mandatory—`config.Config` raises `RuntimeError` if they are missing.

5. **Choose your database**
   - **PostgreSQL (recommended):** Install Docker Desktop, sign in, and ensure the daemon is running. Then:
     ```powershell
     docker compose up -d db redis
     $Env:DATABASE_URL = "postgresql://erp_app:erp_app@localhost:5432/erp?sslmode=disable"
     ```
     An error such as `docker: error during connect: ... pipe ... not found` means Docker Desktop is not running.
   - **SQLite fallback:** For quick smoke tests without Docker,
     ```powershell
     mkdir -Force instance
     $Env:DATABASE_URL = "sqlite:///instance/erp_dev.db"
     $Env:SQLALCHEMY_DATABASE_URI = $Env:DATABASE_URL
     ```
     Alembic now honours these overrides automatically.

6. **Apply migrations and seed demo data (optional)**
   ```powershell
   alembic upgrade head
   $Env:SEED_DEMO_DATA = "1"
   $Env:ADMIN_USERNAME = "admin"
   $Env:ADMIN_PASSWORD = "StrongPass1!"
   python .\init_db.py
   ```
   When using SQLite, deleting `instance\erp_dev.db` resets the schema; the helper script does this automatically if migrations fail.

7. **Run the application**
   ```powershell
   $Env:FLASK_APP = "wsgi.py"
   flask run --port 8080
   ```
   In a second terminal you can start Celery workers if required: `celery -A erp.celery worker --loglevel=info`.

## Troubleshooting
- **`py : The term 'py' is not recognized`** – Install *Python Launcher for Windows* or invoke the interpreter directly (`C:\Path\To\Python311\python.exe -m venv .venv`).
- **`winget` not recognised** – Install the Microsoft Store *App Installer*, or download Python directly as shown above.
- **`alembic upgrade head` fails with `Connection refused`** – Ensure PostgreSQL is running (e.g., `docker compose up -d db`) or export `DATABASE_URL`/`ALEMBIC_DATABASE_URL` to a reachable instance and rerun the migration command.
- **`psycopg2.OperationalError: connection refused`** – Start PostgreSQL or point `DATABASE_URL` to SQLite; Alembic now reads these overrides automatically.
- **`FLASK_SECRET_KEY/SECRET_KEY not set`** – Populate `FLASK_SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `SECURITY_PASSWORD_SALT`, and `JWT_SECRET` in your environment or `.env` before launching Flask.
- **Dependency install tries to compile native extensions** – Confirm you are using the provided lockfile (`pip install -r requirements.lock`) under Python 3.11 with the launcher. Using `requirements.txt` on Python 3.13 will force source builds.
- **`fatal: destination path 'ERP-BERHAN' already exists`** – Remove the existing directory (`Remove-Item .\ERP-BERHAN -Recurse -Force`) or pull the latest changes inside it.

## Next steps
- Run `ruff check .`, `pytest`, and `pip-audit` locally before opening a pull request.
- Review [docs/guided_setup.md](guided_setup.md) for sample data flows and UI tour.
