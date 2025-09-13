# Local Development Quickstart

This quickstart bootstraps a secure ERP-BERHAN dev environment that mirrors production controls.

## Prerequisites
- Python 3.11+
- Docker (for PostgreSQL and Redis)
- Git and GPG configured for signed commits

## Setup Steps
1. **Clone and create a virtualenv**
   ```bash
   git clone https://github.com/getson7070/ERP-BERHAN.git
   cd ERP-BERHAN
   python -m venv .venv
   source .venv/bin/activate
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
5. **Run database migrations and seed an admin**
   ```bash
   scripts/run_migrations.sh
   ADMIN_USERNAME=admin ADMIN_PASSWORD=strongpass python init_db.py
   ```
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
