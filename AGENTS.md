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
