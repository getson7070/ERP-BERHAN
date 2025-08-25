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

## Implementation Roadmap
1. Clean `db.py` and `erp/utils.py` by removing conflict markers and consolidating the PostgreSQL implementation with Redis caching.
2. Replace SQLite-style `?` placeholders in SQL queries with `%s` and update connection logic to use SQLAlchemy’s parameter binding.
3. Run migrations and regression tests across orders, tenders, and analytics modules to confirm PostgreSQL compatibility.
4. Create scaffolding for finance, HR, CRM, procurement, and project management under `erp/routes/` with corresponding templates and tests.
5. Define database schemas and migrations for these modules, ensuring each includes `org_id` for multi-tenant isolation.
6. Update navigation and role-based dashboards to expose new modules based on user permissions.
7. Introduce responsive components and feature parity for mobile by auditing all templates under `templates/`.
8. Implement language packs and a locale selector using Flask-Babel; ensure translations for core pages.
9. Add user-customizable widgets and saved searches within dashboard templates.
10. Introduce FastAPI or Flask-RESTful endpoints under `erp/api/` for orders, inventory, and tenders.
11. Implement webhook support and SDK documentation; integrate with at least one accounting or payment service.
12. Add OAuth2 flows for external systems to authenticate and interact with the ERP.
13. Develop a report builder UI in `templates/analytics/` allowing filter selection and export to PDF/Excel.
14. Add compliance report generators (e.g., tax, HR) in `erp/routes/analytics.py` with supporting migrations.
15. Integrate an anomaly-detection model (e.g., scikit-learn) for sales and inventory forecasting.
16. Implement SSO/OAuth2 providers (e.g., Keycloak) and enforce HTTPS/TLS everywhere.
17. Enable database encryption at rest (PostgreSQL TDE or disk-level encryption) and document key rotation.
18. Expand audit logging to capture every CRUD action with timestamp, user, IP, and store logs in an immutable table.
19. Provide Docker/Kubernetes manifests for API, worker, and bot services with load balancing and failover.
20. Document upgrade procedures using Alembic migrations and rolling deploys.
21. Set up CI/CD pipelines that run tests, linting, and security scans before deployment.
22. Implement a plugin framework allowing modules to register new routes and jobs dynamically.
23. Integrate a task automation engine (e.g., Celery workflows) for reminders and approvals.
24. Evaluate ML libraries for forecasting or chatbot capabilities and expose hooks for AI modules.

## Additional Recommendations
1. UI/UX Review: After implementing changes, run usability tests and lint CSS/JS to ensure responsive design meets industry standards.
2. Compatibility Checks: Update unit and integration tests for all affected modules (auth, db, templates, service worker, etc.).
3. Security Considerations: Perform static analysis and penetration testing around token handling, RLS bypasses, and offline storage.
4. Database Standards: Add migrations and enforce PostgreSQL best practices (constraints, indexes, retention policies); regularly back up and test restores.
