# Module connectivity review

This note summarises the runtime readiness of key ERP-BERHAN modules after
inspecting their blueprints, models, and registration wiring.

## Analytics
- `erp/routes/analytics.py` only exposes a bare `/analytics/dashboard` JSON
  stub and a vitals collector that accepts any payload containing the listed
  Core Web Vitals metrics; it reads reporting data directly from the raw SQL
  connection without schema guards, so the route will succeed even if neither
  orders nor KPI tables exist.
- `erp/analytics/__init__.py` defines a placeholder `DemandForecaster` that
  simply echoes the latest datapoint. No Celery task wiring or integration back
  to sales/orders modules is present, so downstream consumers cannot obtain
  actionable forecasts.

## Approvals
- `erp/approvals/rules.py` only offers helper functions (`approve_doc`,
  `reverse_doc`) without any Flask blueprint or persistence layer. Modules that
  need approval workflows must call these utilities manually, so no web routes
  or event-driven processing exists yet.

## Banking
- `erp/banking/routes.py` exposes authenticated `/banking/accounts` and
  `/banking/statements` endpoints; they commit ORM objects immediately without
  validation or tenant scoping, leaving bookkeeping disconnected from other
  ledgers.
- `erp/banking/models.py` relies on PostgreSQL UUID columns. When the default
  SQLite fallback is active the models fail to create tables, which prevents the
  routes from functioning in development and automated tests.

## Compliance
- `erp/blueprints/compliance/__init__.py` requires Flask-Security token
  authentication and auditor roles, but the application factory never configures
  Flask-Security. API calls therefore abort with `RuntimeError` when the
  decorators resolve the current user.
- The module stores signatures through `erp/compliance/ElectronicSignature` but
  no migration covers the `electronic_signatures` or `batch_records` tables, so
  the code will raise at commit time unless the schema is created manually.

## CRM
- `erp/routes/crm.py` contains a single `/crm/` endpoint returning `'ok'`. The
  CRM package does not expose opportunity, contact, or pipeline handlers, so
  other modules cannot exchange data with CRM.

## Finance
- Multiple blueprints share the `"finance"` name (`erp/finance/__init__.py` and
  `erp/blueprints/finance.py`). When the application auto-registers modules it
  keeps the first blueprint and skips the rest, leaving either the API or the UI
  routes unreachable depending on load order.
- The finance API (`erp/routes/finance.py`) only returns `{"ok": true}` at
  `/api/finance/health`; there are no GL, AR/AP, or posting endpoints to link
  finance with sales, banking, or inventory.

## HR
- `erp/routes/hr.py` exposes `/hr/` with a plain `'ok'` response. HR models
  exist, but no blueprints connect recruitment, onboarding, or performance
  reviews to the UI or REST APIs.

## Inventory
- `erp/blueprints/inventory/__init__.py` implements CRUD with tenant awareness
  via `_resolve_org_id`, but it trusts a raw `session['jwt']` dict without
  verifying signatures or expiry, so any session tampering bypasses tenant
  isolation.
- The SQLAlchemy model (`erp/models/inventory.py`) matches the new Alembic
  migration, yet other inventory packages (e.g. `erp/inventory/routes.py`) still
  manipulate legacy tables (`Item`, `Warehouse`, `StockLedgerEntry`) that do not
  coexist with the new schema, creating conflicting data stores.

## Maintenance
- No maintenance blueprint or model package exists. The analytics placeholder
  references `pending_maintenance` counts, but no module produces or stores that
  data, so the analytics numbers stay at zero.

## Orders
- `erp/routes/orders.py` accepts GET requests on `/orders/` and simply runs
  `SELECT 1`. There is no linkage to the SQLAlchemy `Order` model or to sales
  fulfilment, so other modules cannot create or progress orders through this
  route.

## Sales
- `erp/sales/routes.py` only exposes `/sales/health`. Sales orders are not
  exposed via API endpoints, leaving the sales domain disconnected from finance
  and inventory.

## Supply Chain
- `erp/supplychain/routes.py` supports CRUD for reorder policies but does not
  scope rows by organisation or user; any authenticated user can read or modify
  all policies. The module also lacks integration with inventory usage or
  procurement to keep reorder points in sync.

## User Management
- `erp/user_management/__init__.py` renders `user_management/index.html`, yet
  the templates directory contains no such file. Importing the blueprint raises
  a `TemplateNotFound` error, blocking navigation to the module.
- The blueprint path is absent from `blueprints_dedup_manifest.txt`, so it is
  never registered by the application factory even if the template existed.

## Overall
Many domain packages are placeholders; the blueprints either return static
responses or depend on infrastructure that is not configured (security, schema,
Celery). As a result, the listed modules do not form an interconnected ERP yet—
additional development is required to supply migrations, real endpoints, and
shared service layers before deployment.
