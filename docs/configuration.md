# Configuration Options

This document lists newly added configuration options to enable advanced security, authentication, plugin isolation, support resources, and licensing controls.

## Encryption & Security

- **ENCRYPTION_AT_REST_ENABLED** – Set to `true` to instruct the application to enable encryption at rest. The actual encryption mechanism (e.g., database TDE, disk encryption) must be provided by your deployment infrastructure.
- **ENCRYPTION_KEY_PATH** – Path to the encryption key file or identifier for a key management service. This is used when encryption at rest is enabled.

## Multi‑Factor Authentication (MFA)

- **MFA_ENABLED** – Set to `true` to enforce MFA for all users. The login flow will expect a second factor in addition to a password.
- **MFA_PROVIDER** – Specifies the MFA provider type, such as `totp`, `sms` or `email`.
- **MFA_ISSUER** – Human‑readable issuer name displayed in authenticator apps (e.g., “ERP‑BERHAN”).

## Plugin Isolation

- **PLUGIN_SANDBOX_ENABLED** – When `true`, third‑party plugins will execute in a sandboxed context to prevent them from affecting core functionality or accessing restricted resources.

## Support & Community

- **SUPPORT_PORTAL_URL** – Base URL for the official support portal where users can submit tickets and access help resources.
- **COMMUNITY_FORUM_URL** – Base URL for the community forum where users and developers can discuss features, share tips and provide feedback.

## Licensing & Cost Model

- **LICENSE_MODEL** – Specifies the software license (e.g., `MIT`, `GPL`, or proprietary).
- **COST_MODEL_URL** – Optional URL pointing to documentation of the cost or pricing model for hosted deployments.

### Using these settings

These variables can be defined in your environment or `.env` file. The application reads them via `os.environ.get()` in `config.py`. Adjust them according to your deployment and security requirements.
