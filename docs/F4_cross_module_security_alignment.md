# F4 — Cross-Module Security & Access Control Consolidation

This blueprint strengthens existing RBAC/CSRF foundations by unifying policy enforcement across all entry points while preserving current routes and services.

## Objectives
- Centralize permission decisions for HTTP routes, bots, CLI tools, and Celery tasks.
- Detect and prevent unguarded endpoints or tasks through CI scanning.
- Improve visibility into permission mappings and security regressions.

## Unified Policy Engine
- Provide a single helper (e.g., `can(user, action, resource, context=None)`) consumed by web views, REST endpoints, bots, CLI, and batch jobs.
- Standardize action strings such as `order.create`, `order.approve`, `inventory.adjust`, `report.view`, `banking.sync`.
- Require org scoping and ownership checks inside policy evaluation to avoid cross-tenant leakage.

## Permission Catalog and Diffs
- Maintain a generated catalog mapping roles → permissions; include it in repo (JSON/YAML) for audits.
- Add a tool (`tools/dump_permissions.py`) to dump current mappings; CI can diff to detect unreviewed permission changes.
- Document new permissions alongside feature flags and migrations to keep change history clear.

## Security Tests & Negative Paths
- Expand tests to cover denial paths: unauthorized approvals, inventory edits without role, restricted report access.
- Verify each denial logs audit metadata for monitoring/anomaly detection.
- Ensure Celery tasks and bot handlers are decorated with permission checks (`@require_task_permission`, `@require_bot_permission`).

## Operational Hygiene
- Tie policy changes to rollout plans and UI messaging so users understand access denials (clear dialogs/tooltips).
- Keep migrations additive and org-aware (indexes on `org_id` for security + performance).
- Align with earlier SLO/error-budget rules: if security regressions appear, freeze risky releases until resolved.
