# Integrations & Ecosystem

## REST & GraphQL APIs
- `GET /api/ping` – simple health check.
- `POST /api/graphql` – execute GraphQL queries; try `{ hello }`.

## Webhooks
Set `WEBHOOK_URL` in the environment to forward events. Incoming requests must include an `X-Signature` header with an HMAC SHA-256 digest of the raw body using `WEBHOOK_SECRET` to prevent spoofing.

## SDK
`sdk/client.py` provides a minimal Python interface:
```python
from sdk.client import ERPClient
client = ERPClient('http://localhost:5000')
print(client.ping())
```

## Connectors
- `erp/connectors/accounting.py` – push invoices to accounting software.
- `erp/connectors/ecommerce.py` – fetch products from e-commerce platforms.

## Object Storage
`erp/storage.py` uploads files to S3-compatible backends with a basic EICAR scan and returns presigned URLs for secure downloads.

## Bot Adapters
- `plugins/telegram_bot.py` – links ERP accounts via `/link <token>` and rate-limits requests to curb abuse.

## Plugin Marketplace
Modules placed in the `plugins/` folder with a `register(app)` function are auto-discovered on startup. Visit `/plugins/` to view installed plugins.

### Plugin API & Versioning
- Plugins must expose a `metadata()` function describing name, version, and compatibility range.
- Semantic versioning applies; breaking API changes bump the MAJOR version and are recorded in `CHANGELOG.md`.
- Sandbox plugins by running untrusted code in isolated Celery workers and restricting filesystem access.

### Connector Coverage Matrix
| Connector | Read | Write |
|-----------|------|-------|
| Accounting | ✔️ | ✔️ |
| E-Commerce | ✔️ | ❌ |
| Inventory Scanner | ✔️ | ✔️ |
