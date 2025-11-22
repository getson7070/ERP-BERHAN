# Admin Console, Roles, and MFA

This module adds a secure administration API for employee accounts, role assignment, MFA enrollment, and session revocation.

## Endpoints

- `GET /api/admin/users` – list users with roles, MFA flag, and active status.
- `POST /api/admin/users/<id>/roles/grant` – grant a role (blocks superadmin grants unless caller is superadmin).
- `POST /api/admin/users/<id>/roles/revoke` – revoke a role (blocks removal of the last admin).
- `POST /api/admin/users/<id>/deactivate` / `reactivate` – toggle account status and revoke sessions.
- `POST /api/admin/users/<id>/mfa/init` – returns TOTP secret + provisioning URI.
- `POST /api/admin/users/<id>/mfa/enable` – verify code, enable MFA, and issue backup codes.
- `POST /api/admin/users/<id>/mfa/disable` – disable MFA.
- `GET /api/sso/login` / `callback` – OIDC-ready SSO hooks (use `OIDC_CLIENT_ID/SECRET/METADATA_URL`).

## Data Model

- `User` now stores `is_active` and a relationship to `Role` via `user_role_assignments`.
- `UserMFA` and `UserMFABackupCode` store MFA configuration and recovery codes.
- `UserSession` records active sessions for revocation.

## UX Notes

- MFA enforcement happens during `/auth/login` with support for backup codes.
- Session identifiers are recorded so admin deactivation cleanly logs users out.
- Role assignment APIs return clear JSON errors for UI display (403 on privilege violations).

## Testing

- `tests/test_admin_roles.py` checks privilege escalation blocks.
- `tests/test_mfa_login.py` ensures MFA blocks password-only logins when enabled.
