# System verification snapshot

## Local deployment
- Local Docker workflow remains documented via `README_LOCAL.md`, using `docker compose up --build` with health check and migration commands for reproducible bring-up.
- Security gate and tenant guard share the same health/status allowlist for probes: `/health`, `/healthz`, `/health/live`, `/health/ready`, `/health/readyz`, `/healthz/ready`, `/readyz`, `/status`, `/status/health`, and `/status/healthz` stay reachable for load balancers.

## UI and UX readiness
- Landing and authentication screens use the Bootstrap-based `choose_login.html` layout with dark-mode friendly styles, CTA buttons, and role-specific guidance, aligning UX with industry defaults.
- User-management screens provide accessible labels, help text, and responsive tables for employees, clients, and administrators.

## Authentication, authorization, and user flows
- The authentication blueprint now supports registration, login, logout, and automatic role assignment, seeding employee records and redirecting into analytics dashboards after login. Validation covers missing credentials and duplicate accounts.
- Blueprint discovery intentionally excludes legacy duplicates while auto-registering the curated set of upgraded modules, ensuring the auth routes load alongside analytics, orders, CRM, finance, supply chain, and maintenance.

## Analytics, reporting, and geolocation
- Analytics endpoints collect front-end vitals with optional latitude/longitude and city labels, persisting them in the cross-module `AnalyticsEvent` table and surfacing geo-hotspot counts in the dashboard payload.
- Report builder and KPI endpoints aggregate orders, finance entries, CRM leads, inventory, and maintenance data for connected module reporting.

## Test coverage
- Smoke tests exercise authentication, banking, CRM, sales, analytics, supply-chain policies, and report builder flows using an in-memory database to confirm cross-module links stay functional. All smoke checks pass in the current run.

## Blueprint registration status
- The application factory loads a hardened default configuration, initializes security extensions, and registers the curated blueprint list while skipping legacy CRM and banking duplicates. Duplicate name/prefix pairs are skipped with logging to avoid collisions.
