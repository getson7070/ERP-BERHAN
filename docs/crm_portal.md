# CRM & Client Portal

This document summarizes the CRM and client self-service flows.

## 1. CRM Accounts

- Entity: `CRMAccount`
- Key fields:
  - `pipeline_stage`: `lead` → `prospect` → `client`
  - `segment`: A/B/C or "strategic", "standard", etc.
  - Links to contacts and support tickets.

Endpoints:

- `GET /api/crm/accounts?stage=lead&segment=A` – list with filters
- `POST /api/crm/accounts` – create new account (default stage `lead`)
- `GET /api/crm/accounts/<id>` – details
- `PATCH /api/crm/accounts/<id>` – update core fields

## 2. Pipeline Transitions

- Allowed stages: `lead`, `prospect`, `client`.
- Endpoint: `POST /api/crm/accounts/<id>/advance-stage`
  - Only roles: `crm`, `sales`, `admin`.
  - Records a `CRMPipelineEvent` with `from_stage`, `to_stage`, `reason`.
- History: `GET /api/crm/accounts/<id>/pipeline-events`.

Use this history for conversion analytics and sales performance dashboards.

## 3. Client Portal

- Portal links `User` → `CRMAccount` via `ClientPortalLink`.
- Endpoints:
  - `GET /api/portal/me/account` – account summary for the current portal user.
  - `GET /api/portal/me/tickets` – list support tickets for the account.
  - `POST /api/portal/me/tickets` – create new support ticket.

The portal endpoints are protected by `@require_login` and only reveal data for the linked account.

## 4. Integration Points

- **Marketing & segmentation:** the `segment` and `pipeline_stage` fields can be fed into marketing/analytics modules for campaign targeting and funnel analysis.
- **Support operations:** `SupportTicket` provides a basic ticketing model that can be extended with SLAs, assignments, and integration with external helpdesk tools.
- **Payments & orders:** additional `/api/portal/me/orders` and `/api/portal/me/payments` endpoints can be added to expose sales and finance data to clients once the sales/finance APIs are standardised.
