# F7 — Inventory / Orders / Finance Triangulation & Leakage Prevention

## Purpose
Add a **non-disruptive control layer** that continuously cross-checks Inventory, Orders, and Finance so they cannot drift apart without detection. This blueprint is fully additive to Tasks 1–21 and F1–F6: it wraps existing flows, avoids schema rewrites, and keeps RBAC/CSRF/CI/CD, queue priorities, and circuit breakers intact. The intent is to bring operational confidence from “we think numbers line up” to “we can prove they line up” without slowing users down.

## Design principles
* **Read-only first, no hidden mutations** — validation and reporting jobs do not alter transactional data; fixes are always human-approved.
* **Org-scoped by default** — every query uses org_id filters to avoid cross-tenant leakage.
* **Industry-standard UX** — dashboards show severity badges, filters, drill-downs, and aging to keep operators productive and aligned with modern UI/UX expectations.
* **Secure by construction** — inherits the centralized policy engine, audit logging, and period-close rules; never posts into closed periods.

## Core capabilities
1. **Triangulation engine (hourly/daily background job)**
   * Compares order delivery, inventory movements, and accounting entries for quantity and value parity.
   * Flags mismatches with severity (low/medium/high/critical) and writes reports/alerts only—no data mutation.
2. **Inventory leakage analytics**
   * Detects shrinkage, suspicious adjustments (off-hours, no PO/delivery reference), repeated negative stock, and high-risk users.
   * Uses existing ledgers, adjustments, and audit logs; no schema changes required.
3. **Order consistency validation**
   * Pre-flight checks ensure SKU validity, pricing/discount rules, approval chain compliance, and stock allocation before completion.
   * Blocks completion when delivery, invoicing, or payments are missing unless an approved exception exists.
4. **Finance-to-inventory integrity**
   * Verifies COGS postings align with stock reductions and valuation method (FIFO/LIFO/average) and catches revenue/COGS mismatches.
   * Flags inventory reductions without COGS (or vice versa) and impossible margins or cost drifts beyond tolerance.
5. **Exception suggestions (human-in-the-loop)**
   * Stores reconciliation proposals (e.g., link movements to delivery notes, map invoices to POs) in a dedicated suggestions record for review/approval; never auto-applies fixes.
6. **Timeline verification and fraud/backdating alerts**
   * Checks chronological consistency of created/approved/posted timestamps and raises alerts for backdating or edits after close.
7. **Alerts and dashboards (multi-channel)**
   * Telegram commands (e.g., `/triangulation_today`, `/inventory_leaks`) plus a web dashboard that groups issues by severity and shows aging; provides download/export paths for auditors.
8. **Predictive early-warning signals**
   * Highlights abnormal adjustment rates, after-hours activity, margin anomalies, payment delays, or warehouse-specific spikes as leading indicators of leakage or fraud.

## Operational posture
* **Non-blocking by default**: runs asynchronously via Celery/queues; does not block transactions.
* **RBAC-aligned**: visibility and actions respect centralized policy engine; high-risk resolutions require elevated approvals.
* **Period-aware**: honors soft/hard close rules from finance; never posts into closed periods.
* **Multi-tenant safe**: all queries scoped by org_id; no cross-tenant reads.
* **Security & observability**: emits metrics for mismatch counts, aging, and suggestion backlog; routes anomalies to Prometheus/Sentry without logging sensitive payloads.

## Rollout steps (safe and incremental)
1. Implement read-only triangulation jobs and leakage analytics; surface results via reports/Telegram/dashboard with clear UI cues.
2. Add suggestion capture for mismatches with approval routing; no auto-fix.
3. Tie alerts into existing incident runbooks; define SLOs for mismatch resolution (e.g., 95% critical issues triaged <24h).
4. Gradually expand rule coverage (lots/serials/expiry, multi-bin) based on answers to warehouse/stock detail questions.

## Open questions to refine scope
1. Do you track serials, lots, or expiry, or only quantities? (Impacts triangulation depth.)
2. Are warehouses multi-location/bin? (Impacts leakage detection granularity.)
3. Is negative stock currently allowed intentionally or due to gaps? (Impacts guardrail strictness.)
