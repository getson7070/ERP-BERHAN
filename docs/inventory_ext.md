# Inventory & Warehouse Extensions

## Capabilities
- Multi-warehouse with bins/locations for finer placement control.
- Lot and expiry tracking with per-lot alerts.
- Serial tracking support via `inventory_serials` (model only; wire to intake as needed).
- Concurrency-safe balances + immutable stock ledger for every move.
- Cycle counts with submission/approval and variance posting.
- Auto-reorder rules with background scan and audit logging.
- Manual adjustments endpoint for stress/load harnesses.

## Key Rules
- All stock mutations should go through `erp.services.stock_service.adjust_stock()` to enforce row locks, prevent negatives, and emit ledger entries with idempotency keys.
- Tenant isolation: every query is scoped by `resolve_org_id()` and models carry `org_id` where applicable.
- Negative stock is rejected by default; callers must decide policy before bypassing.
- Cycle count approval posts variances into the ledger using idempotency keys per line.
- Reorder scan writes audit events instead of auto-creating POs; wire into procurement if desired.

## API Endpoints
- Warehouses/Locations
  - `POST /api/inventory/warehouses`
  - `GET /api/inventory/warehouses`
  - `POST /api/inventory/warehouses/<id>/locations`
- Lots & Expiry
  - `POST /api/inventory/lots`
  - `GET /api/inventory/lots/expiring?days=90`
- Cycle Counts
  - `POST /api/inventory/cycle-counts`
  - `POST /api/inventory/cycle-counts/<id>/submit`
  - `POST /api/inventory/cycle-counts/<id>/approve`
- Adjustments
  - `POST /api/inventory/adjust`
- Reorder
  - `POST /api/inventory/reorder-rules`
  - `POST /api/inventory/reorder-scan`

## Tasks
- `erp.tasks.inventory.reorder_scan` — scans active rules and emits audit entries with suggested quantities.
- `erp.tasks.inventory.expiry_alerts` — logs expiring lots within the configurable window (default 90 days).

## Stress Harness
A Locust script can target `/api/inventory/adjust` for throughput/lock testing while `/api/inventory/cycle-counts` and `/api/inventory/reorder-scan` validate concurrency and background automation.
