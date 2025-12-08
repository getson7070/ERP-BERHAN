# Layer 1 Audit – Identity & Access Model

## Scope
This document reviews the current identity and access implementation in ERP-BERHAN against the requested requirements for clients, employees, and administrators (including MFA expectations).

## Current Capabilities
- **Client self-registration & approval queue**: `/auth/client/register` captures TIN (10-digit validation), institution metadata, contact info, address granularity (region/zone/city/subcity/woreda/kebele/street/house number/GPS hint), notes, and a portal password. Submissions are stored as `ClientRegistration` records with `status="pending"`, avoiding duplicates by email/TIN and requiring supervisor approval before activation.【F:erp/routes/auth.py†L88-L233】
- **Login flow with throttling & MFA hooks**: `/auth/login` supports JSON or form login, per-IP rate limiting, email-level cooldown backoff, account activation checks, and optional MFA (TOTP or backup codes) before session creation and audit logging.【F:erp/routes/auth.py†L235-L518】
- **Privileged MFA guard**: A global before-request guard now blocks any admin/management/supervisor role request when MFA has not been verified in the session, returning JSON 403 for APIs and redirecting browsers to login with guidance. Exemptions are limited to auth/health/static endpoints and are configurable via `MFA_GUARD_EXEMPT_ENDPOINTS`.【F:config.py†L51-L69】【F:erp/security.py†L98-L184】【F:erp/__init__.py†L44-L75】
- **MFA data models**: Tables for user-level MFA secrets, backup codes, and session tracking exist with per-org uniqueness, timestamps, and revocation fields, enabling TOTP + backup code flows and session auditing.【F:erp/models/security_ext.py†L12-L66】
- **RBAC policy engine**: A policy-based evaluator supports hierarchical roles, allow/deny rules with wildcards, and contextual conditions (e.g., ownership, warehouse/branch/org scoping, min/max amounts) to enforce least privilege and supervisor/admin distinctions when configured.【F:erp/security_rbac_phase2.py†L1-L117】
- **User entity with role assignments**: The primary `User` model includes unique username/email, active flag, hashed passwords, and many-to-many role assignments via `user_role_assignments`, aligning with Flask-Login integration for session management.【F:erp/models/user.py†L13-L72】

## Gaps & Risks vs. Requirements
- **Multiple user models**: There are two `User` definitions (`erp/models.py` and `erp/models/user.py`), which risks mismatched authentication behavior and schema drift. Clarify and consolidate to a single canonical model before extending roles or MFA enforcement.
- **MFA enforcement for admins**: While MFA is supported, enforcement is optional and not role-gated. The requirement that admin/management logins must include an extra authentication code is not guaranteed; privileged roles only trigger manual approval in self-registration, not mandatory MFA at login.
- **Client contact multiplicity & approval workflow**: The registration flow queues a single contact per TIN; there is no visible mechanism for management-approved multiple contacts under one institution or explicit supervisor approval UI/API.
- **Geo-capture on access**: No geolocation capture is present in login/session creation; location logging for access attempts is not implemented.
- **UI/UX alignment**: The login/registration templates referenced (`login.html`, `client_registration.html`) are not assessed here for modern UX or MFA prompts; no enforcement that dashboards adapt to client vs. employee roles is visible at the routing layer.
- **Role definitions and hierarchy**: RBAC policies exist but default role assignments (e.g., employee vs. supervisor vs. admin) and mappings to required workflows (orders/maintenance/finance) are not codified in this layer. There is no explicit supervisor approval gate for client onboarding or maintenance/order approval in the auth layer.

## Recommendations (Layer 1)
1. **Choose a single `User` schema** and retire the duplicate model to avoid inconsistent queries, migrations, and password hashing. Migrate the database and ORM imports to the canonical model.
2. **Enforce MFA by role**: Require TOTP (or backup code) for admin/supervisor roles on every login and during sensitive actions (session refresh, role changes). Add configuration/DB flags that mandate MFA for privileged roles and validate during `/auth/login` before session issuance.
3. **Support multi-contact clients**: Extend the client onboarding schema to link multiple contacts to a single TIN/institution with approval workflow, and expose supervisor/admin approval routes with audit logging.
4. **Capture geolocation on auth events**: Add optional geolocation fields to login requests and persist them in `UserSession` (or a new `LoginEvent`) for compliance with access-geo tracking requirements.
5. **Harden UI/UX**: Update auth templates to clearly prompt for MFA when enabled, surface cooldown/retry info, and tailor dashboards/menus based on role (client vs. employee vs. admin) immediately after login.
6. **Codify role hierarchy defaults**: Seed base roles (client/employee/supervisor/admin) and RBAC policies that express required separations (e.g., supervisors approve client onboarding, admins manage roles). Integrate `resolve_org_id()` to scope role evaluation across tenants.

## Next Steps
- Align database migrations to the chosen `User` model and enforce unique constraints for TIN-based institutions and multi-contact relationships.
- Add automated tests for MFA enforcement paths, rate limiting, and RBAC rule evaluation for critical resources (orders, maintenance, approvals).
