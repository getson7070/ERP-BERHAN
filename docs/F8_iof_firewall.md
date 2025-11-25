# F8 — Inventory/Orders/Finance Risk Firewall (IOF-Firewall v1.0)

## Purpose and Scope
The IOF-Firewall adds a pre-commit guardrail layer on top of existing Inventory, Orders, and Finance flows to block invalid or high-risk transactions before they reach the database. It is additive and compatible with Tasks 1–21 and F1–F7, preserving current schemas, APIs, and deployment processes while improving safety, auditability, and UX clarity.

## Core Principles
- **Do not rewrite flows:** Wrap existing transaction paths with validation rather than changing their semantics.
- **Tenant isolation first:** All checks run within `org_id` scope; no cross-tenant data access.
- **Least surprise for users:** Hard-block only illegal actions; soft-block provides clear warnings and optional escalation.
- **Human-in-the-loop:** Suggestions and autofixes always require explicit approval.
- **Performance aware:** Inline checks are lightweight; deeper analysis runs asynchronously.

## Universal Pre-Commit Validator
Add a shared entry point `validate_transaction(type, payload)` invoked by critical actions (stock movements, orders, deliveries, POs, invoices, payments, COGS entries, adjustments, returns). Validation occurs before commit and returns one of: `approved`, `blocked`, `warn`, `needs_approval`, `flagged_for_review`.

Checks performed:
- Schema/field sanity and required references present.
- RBAC/permission verification using the central policy engine.
- Period state (open/closed; honors soft/hard close rules).
- Quantity, cost, and price sanity; prevents negative stock unless explicitly permitted.
- Order–inventory alignment (no fulfillment without allocation; no over-delivery).
- Duplicate reference detection.
- Cross-ledger consistency (inventory vs COGS vs invoice/payment links).
- FX rate validity for multi-currency postings.
- Timestamp anomalies (backdating, out-of-order approvals).
- User behavior anomalies (excessive adjustments, after-hours risk).

## Risk Scoring (0–100)
Every transaction is scored before persistence:
- **Inputs:** user history, transaction size, timing, pricing variance, quantity variance, stock constraints, outstanding credit, frequency of adjustments, pattern deviation.
- **Responses:**
  - High (>80): requires multi-level approval; notify admin/bot; log to `risk_events`.
  - Medium (40–80): single approval; queued for daily review.
  - Low (<40): auto-approve unless other rules trigger.

## Hard-Block and Soft-Block Rules
- **Hard-block (deny):** over-delivery vs stock, negative stock attempts, backdating into hard-closed periods, COGS edits in closed months, approvals above threshold without role, invoicing without corresponding stock unless approved exception exists.
- **Soft-block (confirm + notify):** large price deviations, large stock adjustments (>2% warehouse), expiry-based write-offs, payments without invoice link, off-hours risky actions.

## Transaction Lineage
Generate a lineage document for each transaction chain (PO → GRN → stock move → COGS → invoice → payment) stored as JSON for auditability, debugging, and bot/UX summaries. No operational logic change—read-only metadata.

## Behavioral Anomaly Detection
Lightweight analytics (non-ML) to flag anomalies:
- **User:** frequent adjustments, reversals, after-hours activity, risky permission combinations.
- **Warehouse:** repeated shrinkage/returns, negative stock bursts, expired stock spikes.
- **Client:** unusual ordering patterns, chronic credit delays, high cancellation rates.
Alerts route to admins/finance/warehouse managers via dashboards and bots.

## Multi-Layer Approval Engine (Context-Aware)
Approvals consider transaction type, amount, risk score, item type, warehouse, client credit, and user role. Examples: large stock adjustments require warehouse + finance; discounts >10% need sales manager + admin; payments > threshold need finance + executive. Integrates with existing RBAC/approval services; no new schema required.

## Integrity Self-Healing (Human-Approved Suggestions)
When mismatches are detected (from F7 triangulation), propose fixes without auto-applying:
- Link stock movements to delivery notes.
- Create missing COGS entries for invoices.
- Match bank lines to payments with confidence scores.
Actions exposed via bot commands (`/fix_inventory_mismatch <id>`, `/apply_suggestion <id>`) and dashboard buttons; always require approval.

## IOF Firewall Dashboards
Provide Web + Telegram views for:
- Inventory: critical mismatches, adjustment trends, shrinkage hotspots.
- Orders: stuck/risky orders, duplicate detection, underpriced orders.
- Finance: COGS inconsistencies, unmatched payments, FX variance logs.
Include shortcuts `/iof_today`, `/iof_risk_top`, `/iof_pending_actions` for quick ops access.

## UX and Operational Considerations
- Clear, industry-standard UX copy for warnings and approvals; highlight required actions and responsible roles.
- Group and prioritize alerts to minimize fatigue; route to role-appropriate channels.
- Inline validations stay fast; heavy analytics run asynchronously with background queues.
- All rejected/blocked actions are logged for audit and legal defensibility.

## Open Questions (for configuration depth)
1. Should all blocked actions be permanently logged for audit/export? (recommended: yes)
2. Should firewall thresholds (price/stock deviations, risk bands) be configurable via UI settings or remain code-driven? (recommend UI-managed with audit log of changes).
3. What default thresholds should apply per org/warehouse/item class (e.g., critical reagents vs general supplies)?

## Rollout Plan (Safe, Additive)
1. **Dark mode:** enable validator in report-only mode; no blocking, just logging and dashboards.
2. **Soft enforcement:** enable soft-blocks + approvals for high-risk transactions while allowing overrides.
3. **Hard enforcement:** enable hard-blocks for illegal actions once noise is low; keep soft-blocks for edge cases.
4. **Continuous tuning:** review risk scores, thresholds, and anomaly rules monthly; retire noisy rules and codify effective ones.
