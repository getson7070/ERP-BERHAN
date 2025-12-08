# Main Branch Layered Audit (2025-12-12)

This report reviews the current main branch by the 11 functional layers, highlighting what is in place, remaining gaps, and the most critical remediation items. It reflects the latest codebase updates (MFA/RBAC hardening, geo enforcement, procurement trade metadata, readiness checks, and dashboards) and is intended to guide production readiness.

## LAYER 1 – Identity & Access Model (Clients / Employees / Admins)
- **Strengths:** MFA defaults for privileged roles, login flow resets MFA state, privileged routes enforce MFA/session checks. Admin health/dashboard endpoints are MFA-gated.
- **Gaps:** Need continuous MFA coverage audit for legacy endpoints, and clear MFA enrollment UX for first-time admins.
- **Critical actions:** Run end-to-end MFA smoke tests on legacy blueprints; add admin-facing MFA enrollment wizard and backup code export.

## LAYER 2 – Client Onboarding & Approval Workflow
- **Strengths:** TIN validation (10 digits) enforced, duplicate pending registrations blocked, multi-contact onboarding per institution supported with supervisor review messaging.
- **Gaps:** Supervisor approval SLA tracking not surfaced; onboarding audit logs should include geo/context when applicable.
- **Important actions:** Add SLA timers/alerts for pending approvals; extend onboarding form to capture optional geo context for audit.

## LAYER 3 – Employee RBAC & Supervisor vs Admin
- **Strengths:** Default permission matrix boots per-organisation policies; `require_permission` enforces authentication and RBAC; legacy `role_required` now MFA-aware for privileged routes.
- **Gaps:** Policy editor UX exists but needs guardrails (change review, diff preview); broader regression suite for RBAC edge roles is still pending.
- **Critical actions:** Add approval workflow for RBAC policy edits; extend tests for supervisor vs admin boundary cases across approvals, reports, and bot intents.

## LAYER 4 – Orders, Approvals, Commission Logic
- **Strengths:** Commission gating with management approvals; geo metadata enforced on order submissions; dashboards show commission and geo capture status.
- **Gaps:** Credit-sales commission deferral rules need automated settlement linkage; SLA alerts for stalled approvals are not surfaced in UI.
- **Important actions:** Tie commission eligibility to payment settlement events; add supervisor-facing alerting for overdue order approvals.

## LAYER 5 – Maintenance Workflow, Geo, SLA & Escalation
- **Strengths:** Maintenance work orders require lat/lng for start/check-in; SLA due timestamps surfaced in serializers and dashboards for supervisors/techs.
- **Gaps:** Escalation routing and on-call rotations are not configurable; offline geo capture retries not tracked.
- **Important actions:** Add configurable escalation matrix with notification channels; log deferred geo uploads with retry/backfill jobs.

## LAYER 6 – Procurement & Import Tracking
- **Strengths:** Procurement tickets capture PI, AWB, HS code, bank, customs valuation, currency, EFDA reference; milestone geo metadata persisted and validated.
- **Gaps:** Customs valuation workflow lacks approval checkpoints; shipment milestone SLA/ETA tracking not exposed in UI.
- **Important actions:** Add approval stages for customs valuation and bank clearance; surface ETA/SLA risk badges on procurement dashboard cards.

## LAYER 7 – Reporting, Analytics & Performance Evaluation
- **Strengths:** Operations analytics API delivers escalation metrics, SLA risk counts, and lookback windows; dashboards refreshed with live controls; bot activity rollups available.
- **Gaps:** Employee performance scorecards and commission analytics are limited; export/print capabilities are basic.
- **Important actions:** Build per-role performance scorecards (sales, maintenance, procurement) with trend charts; add CSV/PDF export for ops and bot analytics.

## LAYER 8 – Geo Engine & Tracking (Beyond Maintenance)
- **Strengths:** Geo capture enforced for orders, maintenance, and procurement milestones with recorder/timestamp context; dashboards display geo status/accuracy.
- **Gaps:** Institution visit logging for sales reps is not enforced; offline caching/failure telemetry missing.
- **Important actions:** Require geo check-ins for sales/CRM visits; add offline queue with retry visibility and alerts.

## LAYER 9 – Telegram Bot & Automation
- **Strengths:** Webhooks require secrets and allowlists; active-session enforcement with actor logging; org-scoped user/chat bindings; regression tests cover bot security paths.
- **Gaps:** MFA prompts for privileged bot actions are not user-friendly; rate limiting and abuse detection are minimal.
- **Important actions:** Add human-in-the-loop confirmation for high-risk bot commands; implement per-chat rate limits and anomaly alerts.

## LAYER 10 – Database Schema & Alembic (High-Level View)
- **Strengths:** Recent merge migration reconciles prior multi-head drift; health checks validate migration and config readiness; org-scoped fields added for user/bot safety.
- **Gaps:** Historical migrations still contain multiple roots; automated linting of new revisions not in CI.
- **Critical actions:** Consolidate legacy migration roots or document branch mapping; add CI job to run `alembic check`/lint and detect new divergent heads.

## LAYER 11 – Deployment & Production Readiness
- **Strengths:** Dedicated prod/dev compose files with health checks; migration job separated; `/readyz` and admin dashboard expose readiness.
- **Gaps:** No automated rollback/backup validation in pipelines; secrets rotation playbooks absent from repo.
- **Important actions:** Add backup/restore verification step in CI/CD; document secret rotation runbooks and wire health checks into container health probes.

## Top 5 Cross-Layer Priorities
1. Close MFA gaps on legacy endpoints and add admin MFA enrollment UX.
2. Add SLA/ETA alerting for onboarding, orders, maintenance, and procurement milestones.
3. Enable RBAC policy change review/approvals with audit diffs.
4. Enforce geo check-ins for sales/CRM visits with offline retry telemetry.
5. Add CI migration linting to prevent future multi-head drift and validate readiness before deploy.

