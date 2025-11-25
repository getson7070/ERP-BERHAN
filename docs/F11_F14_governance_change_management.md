# F11–F14: Governance, Change Management, and Operational Resilience

This document extends the upgrade roadmap beyond F10, layering additional guardrails without conflicting with the prior 21 tasks or F1–F10. Each section is additive, focused on long-term safety, compliance, and operational stability.

## F11 – Data Governance, Retention, and Legal Defensibility

**Objective:** Ensure data handling, logging, and retention meet legal and operational expectations while avoiding future liability.

**Key actions**
- **Data classification & tagging**
  - Define a lightweight taxonomy: `PUBLIC`, `INTERNAL`, `SENSITIVE_PERSONAL`, `FINANCIAL`, `HEALTH/CONFIDENTIAL`.
  - Attach `data_class` metadata to high-risk models (e.g., `User`, `Client`, `Order`, `InventoryItem`, `LabResult`, `Invoice`, `ReportExport`).
  - Enforce logging rules: never log full payloads for sensitive classes; log IDs and minimal context only.
- **Retention & purge policies**
  - Set per-class retention windows (e.g., audit logs 7–10 years; raw bot messages 1–2 years; failed logins 90 days; transient report exports 30–90 days).
  - Add Celery beat jobs to purge, anonymize, or archive expired records to cheaper storage while preserving auditability.
- **Right-to-forget / export**
  - Provide internal tooling to export all records tied to a person or client.
  - Support pseudonymization (replace names with stable hashes) to retain accounting history while honoring privacy requests.

**Why this is safe**
- Builds atop existing logging and audit frameworks; no model rewrites.
- Reduces risk of sensitive data exposure while supporting compliance inquiries and legal holds.

## F12 – Change Management, Feature Flags, and Backwards Compatibility

**Objective:** Prevent production surprises by controlling rollout and preserving client integrations as the platform evolves.

**Key actions**
- **Feature flag framework**
  - Add `FeatureFlag` model with `key`, `is_enabled`, optional `org_id`, and optional `rollout_percentage`.
  - Provide helpers/decorators to gate new flows without redeploys and an admin toggle UI for controlled rollouts.
- **Versioned APIs**
  - Introduce `/api/v1/...` and `/api/v2/...` patterns; keep deprecated versions stable while migrating clients.
  - Document breaking changes and migration paths; deprecate only after safe adoption.
- **Schema-safe migrations**
  - Enforce two-step migrations: add new columns/indices, deploy code, then drop legacy fields after a cooling period.
  - Integrate with existing Alembic/CI checks so merges fail on unsafe destructive changes.

**Why this is safe**
- Aligns with existing CI/CD and migration discipline; rollouts become reversible and observable.

## F13 – Tenant and User Lifecycle Automation

**Objective:** Make onboarding/offboarding of orgs and staff predictable, auditable, and low-risk.

**Key actions**
- **Tenant provisioning**
  - Provide a single script/admin flow that creates an org, seeds default roles/permissions, and sets up baseline dashboards, bot config, and inventory templates.
- **Tenant offboarding/archiving**
  - Implement a controlled state (`SUSPENDED`/`ARCHIVED`) that blocks logins, orders, banking actions, and bot jobs.
  - Offer export packages (scoped DB slice + reports) and schedule purge/anonymization per F11 policy.
- **Employee lifecycle automation**
  - On `LEFT/TERMINATED`, automatically revoke tokens, disable MFA, reassign approvals/tasks, and notify supervisors about open responsibilities.

**Why this is safe**
- Uses existing multi-org + RBAC foundation; minimizes ghost access and stale data.

## F14 – Operational Playbooks, Guardrails, and Human Factors

**Objective:** Run ERP-BERHAN like a product with defined human roles, UI guardrails, and regular drills.

**Key actions**
- **Operational roles**
  - Define roles such as Release Owner, Incident Commander, Database Steward, Security Champion with clear duties (CI ownership, alert review, permission approvals, report validation).
  - Reflect critical roles in-app where appropriate (flags for approvers/owners) while keeping documentation authoritative.
- **UI guardrails for high-risk actions**
  - Add confirmations and clear impact summaries for inventory adjustments, bulk order actions, report exports, and bank payments.
  - Support optional second-factor checks (admin PIN/MFA) for sensitive flows and ensure every action emits an auditable log entry.
- **Drills and dry-runs**
  - Run quarterly staging drills: backup restore + smoke tests, migration rehearsals, feature-flag rollouts, and recovery exercises.
  - Maintain checklists/runbooks so responsibilities are repeatable across the team.

**Why this is safe**
- Adds UX guardrails and operational clarity without changing core APIs or data models; strengthens human process resilience.

## Alignment with Prior Work
- Fully compatible with the 21 baseline tasks and F1–F10; purely additive.
- Reinforces security (MFA/permissions/logging), data quality (reconciliation/retention), and operational discipline (feature flags, drills, roles).
- Supports UI/UX standards by adding confirmation flows, clear messaging, and administrative toggles for controlled change.

## Implementation Pointers
- Place feature flags and permission checks in shared helpers to avoid route-level drift.
- Extend existing Celery beat schedules for retention, archival, and lifecycle tasks.
- Use staging to rehearse destructive operations and document rollback within the deployment runbooks.
- Keep report/APIs versioned in the registry to ensure analytics and bots consume consistent, auditable definitions.
