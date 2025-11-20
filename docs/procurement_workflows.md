# Procurement & Purchase Orders

This document describes the purchase order (PO) lifecycle implemented under `/api/procurement`.

## 1. Order Lifecycle

Statuses:
- `draft` – created but not submitted.
- `submitted` – awaiting approval.
- `approved` – approved, ready for receipt.
- `partially_received` – some lines received, but not all.
- `received` – fully received.
- `cancelled` – closed without completion.

Transitions:
- `draft -> submitted` via `POST /api/procurement/orders/<id>/submit`
- `submitted/draft -> approved` via `POST /api/procurement/orders/<id>/approve`
- `draft/submitted/approved -> cancelled` via `POST /api/procurement/orders/<id>/cancel`
- `approved/partially_received -> partially_received/received` via `POST /api/procurement/orders/<id>/receive`

## 2. Partial Deliveries and Returns

- **Receive goods** via `POST /api/procurement/orders/<id>/receive`
  - Updates `received_quantity` on lines.
  - Status becomes `partially_received` or `received`.

- **Return goods** via `POST /api/procurement/orders/<id>/return`
  - Updates `returned_quantity`.
  - Does not automatically change overall status (can be extended later).

Both endpoints use row locks (`SELECT ... FOR UPDATE`) to avoid race conditions when multiple users update the same PO.

## 3. Bulk Import / Export

- **Bulk import**:
  - `POST /api/procurement/orders/bulk-import`
  - Accepts multiple POs and their lines in a single JSON payload.

- **Export**:
  - `GET /api/procurement/orders/export`
  - Returns latest POs and lines; UI may convert to CSV/Excel.

## 4. Integration Points

- Inventory:
  - When goods are received, you may trigger stock updates from a Celery task or directly inside `receive_goods()`.
- Finance:
  - When a PO is fully received or invoiced, you may trigger journal entries using the finance API (`/api/finance/journal`) or direct DB integration.

Integration details depend on your organisation’s accounting policies and are intentionally decoupled from the core procurement workflow.
