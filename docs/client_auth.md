# Client Registration & Access

## Features
- OTP-based verification for client onboarding (SMS/email stubs)
- Auto-assignment of the `client` role after verification
- Password-based login, logout, and profile self-service
- Password reset with one-time tokens and session revocation
- OAuth scaffold for Google (extensible to Microsoft)

## Endpoints
- `POST /api/client-auth/register` – register + send OTP
- `POST /api/client-auth/verify` – verify OTP, activate account
- `POST /api/client-auth/login` – client login
- `POST /api/client-auth/logout` – end client session
- `GET /api/client-auth/me` – current client profile
- `PUT /api/client-auth/me` – update email/phone
- `POST /api/client-auth/password/forgot` – request reset token
- `POST /api/client-auth/password/reset` – complete reset
- `GET /api/client-oauth/google/login` – OAuth redirect (when configured)

## Security Notes
- All lookups are tenant-scoped via `resolve_org_id()`.
- OTP and reset tokens are stored hashed; raw values are only sent via the chosen channel.
- Sessions are minimally revoked after password reset; integrate your session store for full invalidation.
- OAuth endpoints gracefully disable when Authlib or provider configs are missing.

## Next Steps
- Connect `_send_sms` / `_send_email` to your gateways.
- Wire `login_user` for OAuth callbacks if you want automatic portal sessions.
- Extend role management or add stronger session revocation depending on your deployment model.
