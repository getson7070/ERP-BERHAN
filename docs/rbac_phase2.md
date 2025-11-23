# Phase-2 RBAC and Policy Engine

This layer extends the existing role checks with policy-driven permissions.

## Capabilities
- Policy registry with priorities and allow/deny effects
- Wildcard resources/actions (e.g., `inventory.*`, `finance.post`)
- Optional conditions (own-only, warehouse/org match, amount ranges)
- Role hierarchy for safe delegation
- Role assignment requests with approvals
- Route/Celery/CLI decorators for uniform enforcement

## Key Endpoints
- `GET/POST/PUT/DELETE /api/rbac/policies` – manage policies and rules
- `POST /api/rbac/role-requests` – request a role
- `POST /api/rbac/role-requests/<id>/approve|reject` – approval workflow

## Integration Points
- Use `@require_permission("resource", "action")` on sensitive routes
- Celery tasks can inherit `RBACGuardedTask` and set `required_permission`
- CLI commands can use `permission_command` decorator
- LDAP/OIDC group mapping can grant roles before policy evaluation

## Fairness & Auditability
- Deny overrides allow to prevent privilege creep
- Policy cache invalidates on CRUD to keep evaluations fresh
- Role dominance rules block lower-privileged admins from escalating others
