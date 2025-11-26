# F17 — Queue Prioritisation & Task Orchestration

This layer is additive to existing architecture (Flask, Celery, Redis/RabbitMQ, Docker, Render) and prior upgrades (F1–F16, 21-task plan). It focuses on routing the right work to the right queues so failures in one area cannot starve critical paths (Inventory, Orders, Reports).

## Goals
- Prioritize critical domain work (Inventory/Orders) over notifications, bots, and heavy analytics.
- Isolate workloads so reporting backlogs cannot block operational tasks.
- Add observability and backpressure to keep queues healthy during spikes or downstream failures.
- Preserve compatibility: no route renames, schema changes, or task signature changes.

## Core Design

### 1) Priority queues
Configure Celery with explicit queues and routing keys:
- **critical**: `erp.orders.tasks.*`, `erp.inventory.tasks.*`
- **default**: `erp.notifications.tasks.*`, `erp.bot.tasks.*`
- **background**: `erp.reports.tasks.*`, `erp.analytics.tasks.*`

Default exchange/queue remain, so existing `.delay()` calls continue to work. Routing maps tasks to queues without renaming modules.

### 2) Worker layout
Run separate workers per queue to prevent starvation:
- `worker_critical` (e.g., 4–8 concurrency)
- `worker_default` (notifications/bots)
- `worker_background` (reports/analytics, lower concurrency)

Scale each independently (e.g., more critical workers during month-end) without altering application code.

### 3) Task classification
Classify by impact, not implementation:
- **Critical**: reserve stock, finalize/ship orders, sync payments that affect ledger or inventory.
- **Default**: user notifications, CRM updates, routine bot responses.
- **Background**: bulk PDF/report generation, heavy analytics, long-running exports.

Existing task signatures stay unchanged; routing handles priority.

### 4) Circuit breakers in tasks
Wrap outbound calls (banking, Telegram, SMS, webhooks, file storage) with a small circuit breaker to avoid cascading retries. When open, fail fast and optionally requeue to background or drop gracefully. Uses Redis/DB state; does not modify business logic.

### 5) Backpressure for noisy producers
Limit per-user/org enqueues for heavy/background jobs (e.g., max N concurrent report jobs). Deny or defer when limits exceeded to protect critical queues. Keys stored in Redis with TTL; integrates with existing rate-limit/perf configs from F16.

### 6) Queue health monitoring
Expose lightweight internal endpoint or Prometheus scrape with queue depths per tier (critical/default/background). Add alerts:
- `critical_queue_depth` sustained > threshold → S2
- `background_queue_depth` sustained > threshold → warning

Leverage existing incident/runbook flow; no schema change required.

### 7) Deployment notes
- Celery config gains `task_queues` and `task_routes`; `task_default_queue` unchanged.
- Docker Compose/Render manifests add dedicated worker processes per queue.
- Backwards compatible with current task names; no code rewrites.

## Expert review prompts
- Are priorities aligned with business SLAs (orders/inventory vs reports)?
- Have load tests validated queue isolation under peak/tender periods?
- Who owns queue taxonomy and routing updates as new modules ship?

## Rollout checklist
1) Add queue/routing config and spin up per-queue workers in staging.
2) Enable circuit breaker wrapper for high-risk integrations.
3) Add backpressure limits for report generation; validate UX messaging.
4) Add queue depth metrics and alerts; document runbook actions.
5) Load-test peak scenarios; adjust worker counts and thresholds.
6) Promote to production with monitoring; revisit taxonomy quarterly.
