# Layer 3 Audit – Employee RBAC & Supervisor vs Admin

## Scope
Assessment of employee role design, supervisor/admin separation, approval controls, MFA enforcement for privileged roles, and UX alignment with the requested RBAC expectations.

## Current Capabilities
- **Role decorators and extraction helpers**: `require_roles` enforces role checks for views/APIs, normalizing role names and redirecting unauthenticated HTML users to login while rejecting unauthorized API calls.【F:erp/security.py†L60-L118】
- **MFA guard for legacy role_required flows**: The legacy `role_required` helper now mirrors the MFA enforcement of `require_roles`, blocking privileged-role access (admin/management/supervisor) when MFA isn’t verified and responding with JSON 403 for API callers.【F:erp/utils/core.py†L44-L115】
- **Policy-based RBAC engine**: The Phase-2 engine loads org-scoped allow/deny rules, supports wildcards/conditions, and hierarchy checks via `role_dominates`, enabling separation between admin/superadmin tiers when policies are configured.【F:erp/security_rbac_phase2.py†L13-L69】【F:erp/security_rbac_phase2.py†L89-L117】
- **Baseline policy bootstrap**: A default permission matrix now seeds org-scoped policies (orders/maintenance/procurement approvals, reporting, bot read actions) when none exist, giving legacy roles safe defaults until administrators curate finer-grained rules.【F:erp/rbac/defaults.py†L6-L72】【F:erp/security_rbac_phase2.py†L13-L76】【F:erp/security_rbac_phase2.py†L78-L120】
- **Role request/approval workflow**: `/api/rbac/role-requests` lets employees request roles; admins/superadmins (and HR for listing) approve/reject with dominance checks to prevent granting higher roles than the approver’s hierarchy allows.【F:erp/routes/role_request_api.py†L21-L110】

## Gaps & Risks vs. Requirements
- **No explicit supervisor tier**: Roles distinguish admin/superadmin/HR but lack a dedicated supervisor role with scoped privileges over orders/maintenance/client approvals; commission and geo-approval paths are not tied to supervisors.【F:erp/routes/role_request_api.py†L41-L110】
- **MFA still optional in some paths**: While `role_required` now enforces MFA for privileged roles, other RBAC surfaces (policy evaluation, role requests) do not yet require MFA freshness checks or step-up prompts on sensitive actions.【F:erp/security.py†L60-L118】【F:erp/utils/core.py†L44-L115】
- **Role/permission catalog missing**: There is no seeded catalog mapping business roles (sales rep, biomedical engineer, cashier, tender, supervisor) to permissions and UI menus; policies exist but default assignments and UX tailoring are absent, risking overbroad or inconsistent access.【F:erp/security_rbac_phase2.py†L13-L117】
- **Geo-logging absent in RBAC decisions**: Access checks do not capture geolocation of privileged actions or approvals; requirement calls for geo capture for access and for employee visits/maintenance actions, but RBAC layer does not enforce or record it.【F:erp/security.py†L60-L118】
- **UI/UX for approvals**: No modern supervisor/admin console is visible that lets supervisors approve client onboarding, maintenance, or delivery with MFA prompts, filters, and audit visibility; current flows rely on backend decorators without UX modernization hooks.【F:erp/routes/role_request_api.py†L41-L110】

## Recommendations
1. **Define supervisor role and policies**: Seed `supervisor` with scoped permissions (approve orders/maintenance/client registrations, assign sales reps) below admin; configure `role_dominates` hierarchy entries and enforce supervisor-only approval flows where required.
2. **Enforce MFA for privileged roles**: Extend `require_roles` or wrap sensitive endpoints with `mfa_required`, making MFA mandatory for admin/supervisor actions (approvals, role grants, commission overrides). Add session claims to confirm MFA freshness.
3. **Publish a role catalog**: Create a configuration/migration that seeds business roles (sales rep, accountant tiers, biomedical engineer, cashier, tender, dispatcher, supervisor, admin) with RBAC policy rules and menu visibility; ensure UI navigation respects these mappings.
4. **Geo-audit privileged actions**: Require geo metadata on approval/role-grant requests and persist to audit logs; add middleware to capture location/IP for privileged endpoints to meet access-geo requirements.
5. **Supervisor console UX**: Build responsive dashboards for supervisors/admins with MFA prompts, filters/search, bulk approvals, and contextual audit trails; ensure accessibility and mobile readiness to meet modern UX standards.
