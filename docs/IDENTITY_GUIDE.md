# Authentication and Identity

This guide summarizes the project's authentication architecture.

## OAuth2 with PKCE
- Authorization code flow uses a S256 PKCE challenge to protect public clients.
- Code verifiers are stored in the user session and redeemed during the token exchange.

## WebAuthn Passkeys
- Users can register platform authenticators to create public key credentials stored in the `webauthn_credentials` table.
- Authentication challenges are generated server side and verified using the `webauthn` library.

## MFA and NIST 800-63
- Passwords are hashed with Argon2 and MFA defaults to TOTP in line with NIST 800-63 guidelines.
- WebAuthn authenticators satisfy phishing-resistant MFA requirements.

## JWT Key Rotation and Revocation
- JWTs are issued with a `kid` header tied to the active key in `JWT_SECRETS`.
- A `scripts/rotate_jwt_secret.py` helper promotes new keys.
- Access tokens can be revoked by POSTing to `/auth/revoke`; revoked `jti` values are cached in Redis for the configured TTL.
