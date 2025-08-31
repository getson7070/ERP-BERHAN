# Integrations & Ecosystem

## REST & GraphQL APIs
- `GET /api/ping` – simple health check.
- `POST /api/graphql` – execute GraphQL queries; try `{ hello }`.
- `POST /api/integrations/events` – send integration events.
- `POST /api/integrations/graphql` – query the integration schema.

## Webhooks
`POST /api/integrations/webhook` receives manufacturing and order events. Clients must sign the raw JSON payload with `WEBHOOK_SECRET` and supply the hex digest via the `X-Signature` header to avoid spoofing.

## SDK
`sdk/client.py` exposes helpers for pings, event submission and signed webhooks:
```python
from sdk.client import ERPClient
client = ERPClient('http://localhost:5000', token='API_TOKEN')
client.send_event('order.created', {'id': 1})
client.send_signed_event('order.created', {'id': 1}, secret='WEBHOOK_SECRET')
```

## Connectors
- `erp/connectors/accounting.py` – push invoices to accounting software.
- `erp/connectors/ecommerce.py` – fetch products from e-commerce platforms.
- `erp/integrations/powerbi.py` – fetch Power BI embed tokens for dashboards.

## Object Storage
`erp/storage.py` uploads files to S3-compatible backends with a basic EICAR scan and returns presigned URLs for secure downloads.

## Bot Adapters
- `plugins/telegram_bot.py` – links ERP accounts via `/link <token>` and rate-limits requests to curb abuse.

## Plugin Marketplace
Modules placed in the `plugins/` folder with a `register(app)` function are auto-discovered on startup. Visit `/plugins/` to view installed plugins.
