# Agent Instructions

## Remote connection
- Ensure the `origin` remote points to `https://github.com/getson7070/ERP-BERHAN.git`.
- Authenticate pushes using the `getson7070` account and personal access token.
- If the remote is missing, configure it with:
  `git remote add origin https://getson7070:<PAT>@github.com/getson7070/ERP-BERHAN.git`
- After running required checks, push updates to the `main` branch:
  `git push origin HEAD:main`

## General Guidelines
- Maintain UI/UX to industry standards with responsive Bootstrap layouts, multilingual support, and role-based dashboards.
- Update all affected files and tests to keep modules compatible.
- Guard against security vulnerabilities; enforce HTTPS, OAuth/SSO, RLS, audit logging, and encryption.
- Keep the database at high standards using migrations, constraints, indexes, backups, and tested restores.
- Blueprints exposing a module-level `bp` under `erp/` and `plugins/` are auto-registered; see `docs/blueprints.md`.
- Templates must extend `base.html` and include `_navbar.html`; see `docs/templates.md`.
- Consult `docs/audit_summary.md` for current development gaps and planned improvements.
### Current Key Action Items
- Add missing ERP modules under `erp/routes` with `org_id` schemas and role-based navigation.
- Expand `docs/` with migration guides, training tutorials, and onboarding checklists.
- Build a plugin registry with chatbot/RPA hooks and starter ML forecasting features.
- Document failover procedures, rolling upgrades, and load-testing for Kubernetes manifests.


## Phase-by-Phase Update & Implementation Plan
1. Foundation & Security
   - Add SSO/OAuth2, enforce HTTPS, implement row-level security and audit logs.
   - Strengthen password hashing, secrets management, and encryption at rest.

2. Database & Infrastructure
   - Document backup/restore procedures and connection pooling.
   - Provide HA/auto-scaling manifests and benchmark performance at scale.

3. Automation & Analytics
   - Expand Celery workflows for approvals and reminders.
   - Introduce report builder, forecasting models, and compliance report generators.

4. UI/UX Modernization
   - Refactor all templates for responsive Bootstrap, multilingual support, and role-based dashboards.
   - Ensure mobile/web parity and offline sync consistency.

5. Integration & Ecosystem
   - Expose REST/GraphQL APIs, webhooks, and SDKs.
   - Add third-party connectors (accounting, e-commerce), bot interfaces, and plugin marketplace.

6. Feature Expansion & Adoption
   - Scaffold finance, HR, CRM, procurement, manufacturing, and project modules with tests.
   - Prepare migration guides, training materials, and gather case studies.

## Mandatory Implementation Points
1. Provide module blueprints under `erp/routes/` for finance, HR, CRM, procurement, and projects; include templates, database schemas with `org_id`, and role-based navigation entries.
2. Store workflow definitions in the database with an admin UI to enable or disable modules and customize approval steps.
3. Publish an architecture guide detailing horizontal scaling, load balancing, and database sharding strategies.
4. Deliver customizable dashboards with widgets and saved searches per role; ensure templates extend `base.html`.
5. Use Flask-Babel for translations, audit templates for responsiveness, and ensure the service worker handles offline actions consistently on mobile.
6. Create `erp/api/` using FastAPI endpoints, webhook support, and connectors for accounting and e-commerce systems.
7. Implement bot adapters (Telegram/Slack) and a plugin loader that registers routes and jobs dynamically.
8. Build a drag-and-drop report UI, support PDF/Excel export, and integrate anomaly-detection models for KPI forecasting.
9. Add tax and HR compliance generators in `erp/routes/analytics.py` with supporting migrations.
10. Integrate Keycloak/OAuth2, enforce HTTPS, and enable PostgreSQL TDE or disk-level encryption with documented key rotation.
11. Apply PostgreSQL RLS policies per `org_id` and log all CRUD operations with user, timestamp, and IP.
12. Draft policies aligning with ISO 27001/GDPR and plan for external audits.
13. Provide Docker/Kubernetes manifests with failover, health checks, and documentation for rolling upgrades and rollbacks.
14. Supply load-test scripts and monitor metrics to validate system behavior under high user and data volumes.
15. Produce comprehensive developer and user guides, API references, and set up a discussion forum or issue tracker guidelines.
16. Maintain a plugin registry and expose hooks for RPA/chatbot modules; add starter ML forecasting integration.
17. Offer domain-specific configurations (e.g., healthcare, retail) with tailored schemas and workflows.
18. Document data import steps, provide onboarding tutorials, and publish quick-start videos.

## Additional Recommendations
1. UI/UX Review: After implementing changes, run usability tests and lint CSS/JS to ensure responsive design meets industry standards.
2. Compatibility Checks: Update unit and integration tests for all affected modules (auth, db, templates, service worker, etc.).
3. Security Considerations: Perform static analysis and penetration testing around token handling, RLS bypasses, and offline storage.
4. Database Standards: Add migrations and enforce PostgreSQL best practices (constraints, indexes, retention policies); regularly back up and
5. test restores.

5. **Licensing & Cost Model**: Add a `LICENSE` file (e.g., MIT or GPL) and provide a cost model for SaaS or self‑hosted deployments, including third‑party dependencies.
6. **Deep HR & Manufacturing**: Expand HR modules to include recruitment, onboarding, performance reviews, and payroll, and extend manufacturing with bills of materials, production planning, and quality control.
7. **Advanced UI/UX Customization**: Provide configurable dashboard widgets, interactive charts, real‑time notifications, and no‑code query builders for saved searches.
8. **Third‑Party Integrations**: Build connectors for payroll, marketing, BI tools, and logistics services, and enhance the marketplace UI with curated connectors and ratings.
9. **Automated Deployments & Rollbacks**: Implement blue‑green or canary deployment pipelines, integrate CI/CD with rollback support, and use infrastructure as code (Terraform or Helm).
10. **Compliance & External Audits**: Achieve ISO 27001/GDPR compliance by implementing encryption at rest, data retention policies, secrets rotation, and regular penetration tests.
11. **Community & Support**: Define SLA policies, create issue templates, establish a community forum and knowledge base, and share success stories and change‑management tools.
