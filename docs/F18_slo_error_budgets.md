# F18 — SLOs, Error Budgets, and Release Guardrails

This blueprint defines how to prove reliability for ERP-BERHAN by attaching service-level objectives (SLOs) and error budgets to high-risk modules before shipping new changes. It is additive to all prior upgrades (including the 21 tasks and F1–F17) and does not change runtime behaviour; it establishes contracts, checks, and guardrails.

## 1) Risk zones and target SLOs

Use risk zones to avoid per-endpoint chaos and to align technical SLOs with business impact:

- **Zone A – Critical:** Inventory, Orders, Billing/Finance
  - Availability: 99.5% monthly success (2xx/3xx)
  - Latency: 95th percentile < 1.5s
  - Error rate (5xx): < 0.3%
- **Zone B – Important:** Banking integration, Bot/Telegram, CRM
  - Availability: 99.0%
  - Error rate (5xx): < 1%
- **Zone C – Heavy/Non-urgent:** Reports, Analytics, Bulk exports
  - Job completion SLA: 90% of report jobs < 15 minutes

Document these in `/docs/slo.md` (or equivalent) with mapping from metrics/endpoints to zones and explicit consequences when SLOs are missed.

## 2) Metrics mapping (Prometheus first-class)

Reuse existing metrics and label them by zone:

- HTTP metrics: `http_requests_total{module="orders"}` and `http_requests_total{module="inventory"}` → Zone A.
- Queue metrics: `celery_tasks_completed_total{queue="background"}` and `celery_tasks_failed_total{queue="background"}` → Zone C.
- Banking/bot metrics: map to Zone B.

Define an error budget per zone (e.g., Zone A allows 0.5% downtime/month). When the budget is exhausted, feature releases that touch that zone are paused until reliability is restored.

## 3) CI/release guardrails

Add a lightweight CI job (e.g., `check_slo_budget`) that queries Prometheus for current error budget burn. Behaviour:

- If error budget for Zone A is below threshold → fail or warn in deploy workflow for Inventory/Orders/Billing changes.
- If Zone C budget is low → block/report-heavy deploys until stabilized.

This complements existing pipelines and does not alter application code.

## 4) Operational flow

1. Publish SLO tables and responsibilities in `docs/slo.md`.
2. Add alert rules so SLO breaches trigger incidents and enter post-incident review.
3. Tie release approvals to error budget status (informal discipline or formal CI gate).
4. During breach, only hotfix/reliability changes ship for the affected zone.

## 5) Expert challenges and mitigations

- **Are SLOs real or aspirational?** Start conservative, then tighten once data shows headroom.
- **How to keep SLOs current?** Assign ownership per zone; review monthly in ops meeting.
- **Will SLO gates block the business?** Define exception handling with explicit approvals and time-boxed overrides recorded in audit logs.
