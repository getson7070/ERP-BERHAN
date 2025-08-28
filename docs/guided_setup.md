# Guided Setup

Follow these steps to spin up a demo instance with sample data:

1. **Clone and install**
   ```bash
   git clone https://github.com/getson7070/ERP-BERHAN.git
   cd ERP-BERHAN
   pip install -r requirements.txt
   ```
2. **Start services**
   ```bash
   docker compose up -d db redis
   ```
3. **Run migrations**
   ```bash
   flask db upgrade
   ```
4. **Seed sample organization**
   ```bash
   python init_db.py
   ```
   This creates an `admin` user with password `admin` for the `Acme Pharma` org.
5. **Launch the app**
   ```bash
   flask run
   ```
6. **First-run tour**
   Log in with the seeded admin account and follow the [onboarding tour](onboarding_tour.md).
   Explore inventory, try saved views, and review the analytics dashboard.
