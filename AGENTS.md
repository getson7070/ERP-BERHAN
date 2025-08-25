# Agent Instructions

## Remote connection

- Ensure the `origin` remote points to `https://github.com/getson7070/ERP-BERHAN.git`.
- Authenticate pushes using the `getson7070` account with a personal access token.
- If the remote is missing, configure it with:

  `git remote add origin https://getson7070:<PAT>@github.com/getson7070/ERP-BERHAN.git`

- After running required checks, push updates to the `main` branch:

  `git push origin HEAD:main`

## UI/UX & Feature Checklist
When modifying templates or front-end behavior, confirm the following:
- All templates use industry-standard Bootstrap layouts with client-side validation and responsive design.
- Dashboards remain clean and modular with smart navigation to ensure consistency and familiarity.
- Interfaces support responsive design and mobile-friendly actions.
- The broader system roadmap accounts for:
  - Task & workflow automation
  - Data entry optimization
  - Visualization & reports
  - Role-based access control
  - Error handling & guidance
  - Calendar integration
  - Chat/collaboration within the ERP
  - Offline mode with automatic sync
  - AI-powered recommendations

## Project Phases
1. Foundation & Security
   - Strengthen core authentication, authorization, and data protection.
   - Centralize secrets and enforce HTTPS/TOTP.
   - Implement role-based access control (RBAC).
2. Database & Infrastructure
   - Ensure migration safety, backups, and cloud readiness.
   - Adopt Alembic migrations and pooled connections.
   - Provide backup and restore tooling.
3. Automation & Analytics
   - Automate tender lifecycle, reporting, and scheduled jobs.
   - Expand tender automation.
   - Build analytics dashboard.
4. UI/UX Modernization
   - Apply industry-standard layouts and client-side validation.
   - Refactor templates to responsive Bootstrap.
   - Ensure all templates extend `base.html` or `base_auth.html` and forms use `needs-validation` with `novalidate`.
5. Monitoring & Reliability
   - Introduce observability, crash handling, and self-healing.
   - Add structured logging and health checks.
   - Automate backups and restart policies.
6. Feature Expansion
   - Extend ERP functionality for broader coverage.
   - Enhance HR and document generation.

## Upcoming Requests
1. Replace SQLite usage in `db.py` with SQLAlchemy pointing to PostgreSQL.
   - Introduce Redis connections for caching and task queues; update Celery config accordingly.
   - Provide Alembic migrations for the new schema and update `REQUIREMENTS.txt`.
2. Create `organizations`, `roles`, `permissions`, and `role_assignments` tables in `init_db.py`.
   - Add `org_id` columns to business tables (`orders`, `tenders`, `inventory`, etc.).
   - Update `erp/utils.py` decorators to check role/permission mappings per organization.
3. Introduce an `/auth/token` endpoint in `erp/routes/auth.py` issuing JWT access/refresh tokens.
   - Configure PostgreSQL row-level security policies tied to `org_id` and user roles.
   - Ensure admin logins require TOTP; rotate tokens via environment-managed secrets.
4. Add a WebSocket server (e.g., Flask-SocketIO) for pushing live KPIs.
   - Create SQL materialized views for key metrics and schedule periodic refresh.
   - Update dashboard templates under `templates/analytics/` to subscribe to WebSocket updates.
5. Introduce structured logging (e.g., `logging.config.dictConfig`) in `erp/__init__.py`.
   - Instrument metrics with a library like `prometheus_client`; expose `/metrics`.
   - Configure error monitoring and distributed tracing (e.g., Sentry, OpenTelemetry) for API and Celery tasks.
6. Refactor templates under `templates/` to ensure mobile-responsive design with Bootstrap.
   - Add service worker & IndexedDB logic in `static/js/` for offline data capture and sync endpoints.
   - Document offline sync strategy and user flow in project docs.
7. Add a storage layer (e.g., `storages/s3.py`) using boto3.
   - Update forms and routes handling uploads to persist files in S3 and store URLs in DB.
   - Configure credentials via environment variables and document in README.md.
