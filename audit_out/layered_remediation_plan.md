# Layered Remediation Plan (Critical → Important → Medium)

This plan sequences the remediation work derived from the 11-layer audits so delivery starts with the highest-risk and highest-impact fixes. Each item notes the affected layers, UX/security/database considerations, and key dependencies. Use this list to create timeboxed epics and track completion evidence in the corresponding audit files.

## Critical (start immediately)
1) **Enforce MFA + secure authentication flows**  
   - Layers: 1 (Identity & Access), 3 (RBAC), 9 (Telegram), 11 (Deployment).  
   - Actions: require MFA for admins/supervisors; add pre-auth rate limiting and CSRF on login/registration/bot endpoints; ensure Telegram bot actions require authenticated session tokens.  
   - UX: modern responsive auth screens with inline validation and accessibility labels.  
   - Database: persist MFA secrets/recovery codes with encryption at rest; seed admin roles with enforced MFA flag.

2) **Role/RBAC hardening with tenant isolation**  
   - Layers: 1, 3, 4 (Orders/Commission), 5 (Maintenance), 6 (Procurement), 7 (Reporting).  
   - Actions: implement permission matrix stored in DB; enforce `resolve_org_id()` scoping on all queries; add supervisor vs admin policy gates for approvals; add audit logs for privilege changes.  
   - UX: surface denied-access states with consistent UI patterns and audit trail links.  
   - Database: add `permissions`, `role_permissions`, and `user_roles` tables plus Alembic migrations; backfill legacy roles safely.

3) **Client onboarding validation and approval control**  
   - Layers: 2 (Onboarding), 4, 5.  
   - Actions: require TIN (10 digits) uniqueness; enforce institution-level approvals; support multiple contacts per TIN with manager approval; block unapproved clients from orders/maintenance.  
   - UX: guided registration wizard with clear error states; responsive forms; geo-consent prompts.  
   - Database: unique index on TIN; tables for institution contacts and approval status history.

4) **Geo capture and auditability for field actions**  
   - Layers: 5 (Maintenance), 8 (Geo Engine), 4 (Orders), 6 (Procurement).  
   - Actions: require geolocation for visits/maintenance tickets/procurement milestones; store timestamps, accuracy, and actor; add SLA breach alerts.  
   - UX: map-based check-in UI with permission prompts and offline-friendly retry.  
   - Database: geo columns with indexes; retention and privacy redaction policies.

5) **Secure deployment baselines**  
   - Layers: 10 (DB/Alembic), 11 (Deployment).  
   - Actions: fail fast when `SECRET_KEY`/`DATABASE_URL` missing; enforce TLS, security headers, and secret management via env/vault; add health checks for migrations/backups.  
   - UX: admin banner for maintenance/rollback states.  
   - Database: migration guardrails, PITR drills, and schema linting in CI.

## Important (start after critical underway)
1) **Order/commission correctness and approvals**  
   - Layers: 4.  
   - Actions: differentiate client-initiated vs rep-initiated orders; block commission until payments clear for credit sales; allow management override to assign commission; tie approvals to supervisor roles.  
   - UX: timeline view for approvals/payments; clear commission status badges.  
   - Database: commission ledger with payment-status linkage and audit trail.

2) **Maintenance workflow modernization**  
   - Layers: 5.  
   - Actions: SLA timers, escalation rules, and reminder jobs; enforce geo check-ins; integrate complaint/help desk linkage.  
   - UX: Kanban/board view with SLA badges; mobile-friendly service forms.  
   - Database: ticket status history table with SLA breach markers.

3) **Procurement/import milestone tracking**  
   - Layers: 6.  
   - Actions: milestone states (PO, shipment, customs, delivery); approvals gated by supervisor; geo events for custody transfers.  
   - UX: milestone progress tracker; exception alerts.  
   - Database: procurement events table with attachments/geo metadata.

4) **Reporting, analytics, and performance scorecards**  
   - Layers: 7.  
   - Actions: build scorecard engine for employees; dashboards for client onboarding, orders, maintenance, procurement; role-based visibility.  
   - UX: modern dashboards with export/share; dark mode and accessibility.  
   - Database: materialized views or summary tables; scheduled refresh jobs.

5) **Telegram bot hardening and workflow parity**  
   - Layers: 9.  
   - Actions: align bot intents with web workflows; enforce auth tokens and rate limits; add audit logs; support approval actions with MFA challenge links.  
   - UX: concise prompts with fallback web links; error handling for offline/invalid states.  
   - Database: store bot session bindings with expiry and org scoping.

## Medium (start after critical/important in progress)
1) **UI/UX modernization across modules**  
   - Layers: 1–9.  
   - Actions: adopt shared design system (responsive grid, forms, tables, toasts); add accessibility (WCAG AA), localization, and consistent error handling; refresh dashboards with modern charts.  
   - Database: ensure locale/theme preferences stored per user without weakening security defaults.

2) **Operational runbooks and observability**  
   - Layers: 7, 10, 11.  
   - Actions: document SLOs, alerts, and runbooks for orders/maintenance/procurement; expand OpenTelemetry spans, metrics, and logs; add synthetic checks for auth, onboarding, and geo endpoints.  
   - Database: observability tables/retention configs; ensure Alembic revision metadata is monitored.

3) **Data hygiene and retention**  
   - Layers: 1, 2, 4, 5, 6, 7.  
   - Actions: implement retention/archival for geo, audit, and ticket data; add PII minimization and export tooling; validate TIN/email/phone formats and deduplicate institutions.  
   - Database: partition large tables; enforce constraints for uniqueness and referential integrity.

4) **Performance and compatibility tuning**  
   - Layers: 4, 5, 6, 7, 8.  
   - Actions: add caching for heavy dashboards; optimize queries with indexes; ensure background workers scale horizontally; run browser/ mobile compatibility tests for key flows.  
   - Database: index review and query plans; migrate to async workers where beneficial.

## Execution guidance
- Sequence: tackle Critical items first; begin Important streams once Critical implementation is underway and gated behind feature flags; start Medium items after Critical items are merged and Important items have test coverage.  
- Quality gates: require CI for lint/tests/migrations; capture UI screenshots for onboarding/auth/order/maintenance flows; perform security review before enabling MFA/bot changes in production.  
- Evidence: update each layer’s audit file in `audit_out/` with remediation status, links to PRs, and test artefacts; attach migration IDs and deployment dates.  
- Compatibility: ensure database migrations are reversible; provide upgrade notes and fallback toggles; validate API/contract changes with consumers (web, bot, integrations).
