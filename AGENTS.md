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

## Additional Recommendations
1. UI/UX Review: After implementing changes, run usability tests and lint CSS/JS to ensure responsive design meets industry standards.
2. Compatibility Checks: Update unit and integration tests for all affected modules (auth, db, templates, service worker, etc.).
3. Security Considerations: Perform static analysis and penetration testing around token handling, RLS bypasses, and offline storage.
4. Database Standards: Add migrations and enforce PostgreSQL best practices (constraints, indexes, retention policies); regularly back up and test restores.
