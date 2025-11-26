# F6 — Banking, Finance & Reconciliation Automation

This blueprint layers on top of the existing ERP-BERHAN upgrades (21-task baseline, F1–F5) to make money flows deterministic, auditable, and recoverable without breaking current APIs, bots, RBAC, CI/CD, or database contracts.

## Objectives
- Keep bank → ERP → bots → reports reconciled with zero silent mismatches.
- Preserve existing deployments (Flask, Celery, Postgres, Redis, Docker/Render) and avoid breaking schemas or routes.
- Strengthen security, UX, and data quality standards while keeping performance guardrails.

## Scope & Compatibility
- **Additive only**: no removal of tables, APIs, or deployment patterns; compatible with CI/CD, RBAC/CSRF, feature flags, queues, circuit breakers, and approval flows.
- **Security-first**: all automation passes through policy checks, MFA-enforced roles, and audit logs.
- **DB hygiene**: bank data lands in staging tables first; recon/posting uses existing finance/ledger models and preserves ACID semantics.

## F6.1 — Bank Integration Safe Shell
- Support three ingestion modes per bank: API, file upload (CSV/MT940/XLSX), and manual exception entry.
- Normalize every input into a canonical transaction schema (`date`, `amount`, `currency`, `description`, `account`, `counterparty`, `reference`, `raw_data`).
- Track ingestion states: `received → parsed → validated → posted → reconciled` in staging models (e.g., `bank_statement_imports` + `bank_statement_lines`).
- Enforce isolation: nothing posts to GL until validated; staging rows remain queryable for audits.

## F6.2 — Reconciliation Engine (Rules-Based, Idempotent)
- Deterministic matching pipeline with layers:
  - **Exact rules**: amount, currency, ±N-day date window, reference/client match.
  - **Heuristic scoring**: partial references, small amount tolerances (FX fees), known counterparties.
  - **Unmatched** → `suspense` for human review.
- Each match links `bank_line ↔ payment/receipt/invoice/order` and posts bank fees / FX gain-loss as needed.
- Idempotency keys on batches (e.g., `bank:<conn>:<date>:<window>`) to prevent duplicate postings.

## F6.3 — Finance Integrity Checks
- **Order → Invoice → Payment**: no order closes unless invoiced and paid/approved credit.
- **Stock & COGS**: delivery triggers stock decrease, COGS recognition, and revenue recognition; reconcile movement vs accounting entries.
- **Bank ↔ GL**: reconciled bank lines sum to GL bank accounts within tolerance; raise integrity alerts when off.
- **Multi-currency**: consistent FX tables; differences booked to FX gain/loss with provenance.

## F6.4 — Finance Automation with RBAC & Bots
- Automation proposes; humans approve. Suggested matches carry confidence scores; posting requires role-based approval thresholds.
- Bots act as assistants: `/reconcile_today` lists suggestions for approve/reject/relink; email fallback for outages.
- Approval thresholds: small fees auto-post; medium amounts need finance role; large amounts require dual approval. All actions are idempotent and audited.
- SLA monitor: e.g., 95% of bank lines reconciled within 3 days; alerts fire when backlog grows.

## F6.5 — Period Closing & Locks
- **Soft close**: edits allowed but logged with justification; finance receives adjustment report.
- **Hard close**: no postings/edits via UI, bots, or workers; only super-admin/runbook path with incident log.
- Automation respects locks: posts into current open period or queues for finance review when target period is closed.

## F6.6 — Finance Observability & UX
- Dashboards: reconciliation backlog (total/matched/unmatched/aged), period health (orders vs invoices vs receipts; revenue vs COGS vs margin), FX deltas.
- Alerts: aged unmatched lines, closed-period modifications, reconciliation throughput drops.
- UX: clear confirmation and error states for approvals, reconciliation review screens, and bot prompts; consistent pagination and loading states per UX guidelines.

## Rollout Steps (Safe Adoption)
1. Implement safe shell + staging ingestion; expose reconciliation backlog dashboards.
2. Enable deterministic matching with confidence scoring; keep posting manual initially.
3. Add bot/email assistance for approvals; respect approval thresholds and period locks.
4. Turn on auto-approve for low-risk items once monitoring proves stable.
5. Tie integrity/observability alerts into SLO/error-budget guardrails (F18) and queue priorities (F17).

## Open Questions
- Which banks/formats are active (API vs file) today?
- Do you already enforce monthly closes, or are historical periods still editable?
- Should bots ever auto-approve very small fees (e.g., <1000 ETB), or remain suggestions only?

## Direct Download
The file is available at `docs/F6_banking_finance_reconciliation_automation.md`.
