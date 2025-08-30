# Guided Setup

Follow these steps to bring up a demo environment with sample data.

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # Optional: tools for tests and linting
   pip install -r requirements-dev.txt
   ```
2. **Start services**
   ```bash
   docker compose up -d db redis
   ```
3. **Run migrations and seed data**
   ```bash
   alembic upgrade head
   SEED_DEMO_DATA=1 ADMIN_USERNAME=admin ADMIN_PASSWORD=strongpass python init_db.py
   ```
4. **Load sample organization**
   ```bash
   python scripts/import_fineto.py
   ```
5. **Launch the app**
   ```bash
   FLASK_DEBUG=1 flask run  # auto-reloads templates during development
   ```
6. **First-run tour**
   Log in with the seeded admin account and follow the [onboarding tour](onboarding_tour.md) to explore saved views, breadcrumbs, and other power-user features.
