# Required Secrets

The application retrieves all sensitive configuration exclusively from AWS Secrets Manager or Systems Manager Parameter Store. No default secrets are committed to the repository or provided via plaintext environment variables.

| Secret | Purpose |
| --- | --- |
| `FLASK_SECRET_KEY` | Session and CSRF signing key |
| `WTF_CSRF_SECRET_KEY` | Dedicated Flask-WTF CSRF signing key (falls back to `FLASK_SECRET_KEY` if unset) |
| `JWT_SECRETS` / `JWT_SECRET_ID` | Map of versioned JWT signing secrets with active key id |
| `DATABASE_URL` | PostgreSQL connection string (use `?sslmode=require`; application fails to start if unset) |
| `REDIS_URL` | Redis/ElastiCache connection string |
| `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET` | Credentials for SSO/OAuth2 login |
| `WEBHOOK_SECRET` | HMAC secret for verifying inbound webhook payloads |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credentials for AWS APIs (only when required) |

Secrets must be injected at runtime by the platform (e.g. App Runner or Kubernetes) and rotated per the process in [`docs/security/secret_rotation.md`](security/secret_rotation.md). A pull request introducing a new secret must update this table and document its rotation strategy.
