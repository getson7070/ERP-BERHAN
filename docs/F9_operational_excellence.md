# F9 — Operational Excellence & Chaos Resilience

This blueprint layers on top of the 21-task upgrade and F1–F8 to make ERP-BERHAN resilient when dependencies fail. All items are additive and avoid breaking existing flows.

## Objectives
- Detect and contain third-party or infrastructure failures before they corrupt Inventory, Orders, Finance, or Reporting.
- Degrade gracefully with safe fallbacks instead of crashing or flooding failing services.
- Recover automatically with visibility for SRE/operations.

## A. Circuit Breakers
- Implement a reusable circuit helper (`erp/core/circuit.py`) with closed/open/half-open states, failure thresholds, and reset timers.
- Wrap risky integrations (banking APIs, Telegram/SMS, cloud uploads, webhooks) to stop repeated failing calls and return degraded responses.
- Record breaker transitions and causes for audit/alerting.

## B. Graceful Degradation
- Define per-service fallbacks: manual bank statement upload, email alerts when Telegram is down, local task queue fallback when Redis is unavailable, cached inventory snapshots when DB is slow.
- Preserve data integrity: never apply partial mutations when a dependency is unavailable; queue actions instead.

## C. Watchdogs & Heartbeats
- Scheduled health probe (1–5 minutes) checks DB latency, Redis ping, banking/Telegram reachability, Celery worker heartbeat, bot queue depth, reconciliation backlog, and host resources.
- Persist results to `system_health_events` and expose `/internal/health/system` for dashboards and Prometheus scraping.

## D. Dead Man Switch for Workers
- Track worker liveness in `celery_worker_heartbeats` (worker_id, last_seen, load, queue_depth).
- Alert when heartbeat stales; requeue stalled jobs and drain backlogs automatically.
- Integrates with F5 job governance (DLQ/throttling) to prevent stuck bot/automation flows.

## E. Slow Query Detection
- Add `erp/core/sql_monitor.py` using SQLAlchemy event hooks to log queries over a threshold (e.g., 500ms) with statement, duration, user/role, and org scope.
- Feed logs to Prometheus/Sentry for hotspots affecting inventory and order paths.

## F. Automatic Load Shedding
- Rate-limit APIs and defer non-critical tasks under overload; scale worker concurrency where supported.
- Temporarily disable expensive reports; serve cached snapshots where safe.

## G. Chaos Testing (Staging Only)
- Controlled failure drills: DB outage, Redis hang, Telegram timeout, corrupted bank payloads, large bot bursts, circular stock movements.
- Success criteria: no data corruption, no duplicate orders/entries, workers recover, alerts fire with clear root-cause hints.
- Restricted to superadmin/DevOps; never on production.

## H. Snapshot & Restore Sandbox
- `tools/sandbox_restore.py` spins up a sanitized DB snapshot, applies migrations, runs smoke + reconciliation + reporting sanity checks.
- Serves as a pre-production realism testbed before release (aligns with F6 migration safety nets).

## Operational Questions to Resolve
- Define SLOs per surface (e.g., order success rate, bot latency) and who owns them.
- Clarify who may trigger chaos drills and who responds.
- Establish DB backup/restore drills to pair with rollback strategy.

## Rollout Notes
- Start with passive monitoring (watchdogs, slow-query logs), then enable circuit breakers in monitor-only mode.
- Gradually turn on degradation paths and load shedding; document behavior for support teams.
- Schedule periodic sandbox restores and chaos drills as part of release cadence.
