# F5 — Bot & Automation Reliability Layer

This blueprint adds reliability controls for automation channels (e.g., Telegram bots) without conflicting with prior upgrades (21-task hardening, F1–F4). It layers safety around existing bot models such as `BotCommandRegistry`, `BotEvent`, `BotJobOutbox`, `TelegramConversationState`, and `BotIdempotencyKey`.

## Reliability pillars
1. **Input validation shield**
   - Central validator module (e.g., `erp/bot_core/validators.py`) defines schemas per command and normalizes user inputs (phone numbers, dates, quantities).
   - Bot handlers call `validate_payload(command_name, payload)`; invalid payloads are rejected and logged before any side effects.

2. **Command execution sandbox**
   - Dispatcher wrapper (e.g., `erp/bot_core/dispatcher.py`) fetches handlers from the registry, enforces RBAC, idempotency, structured error handling, and routes fatal failures to a dead-letter queue (DLQ).

3. **Conversation state machine**
   - Replace ad-hoc state keys with a bounded machine (e.g., `START → WAITING_INPUT → VALIDATING → CONFIRM → ACTION → DONE`) stored via `TelegramConversationState`.
   - Prevents dangling or looping conversations and ensures consistent recovery after errors.

4. **Job queue governance**
   - Retry policy with exponential backoff and idempotency checks.
   - DLQ model (e.g., `bot_job_dlq`) capturing job ID, reason, payload, timestamp; periodic job `requeue_stuck_jobs()` moves expired in-flight jobs to DLQ.
   - Queue throttling using Prometheus metric `bot_jobs_queued`; pause intake when thresholds (e.g., >50 pending) are exceeded.

5. **Bot ↔ module contracts**
   - Typed interfaces under `erp/bot_core/contracts/` (e.g., `orders.py`, `inventory.py`, `reporting.py`) define request/response dataclasses and constrain integration to approved module entrypoints.
   - Prevents direct ORM/DB access from bot code and stabilizes future API evolution.

6. **Observability**
   - Prometheus metrics: `bot_jobs_queued`, `bot_jobs_processing`, `bot_jobs_failed`, `bot_job_latency_seconds`, `bot_command_count{command=...}`, `bot_failed_command{command=...}`.
   - Sentry traces per job (`op="bot.command"`), enriched `BotEvent` entries with `duration_ms` and success/failure markers.

## Automation middleware (guard layer)
- Wrap every automation entrypoint (bots, web/min-app actions, scheduled jobs) with a guard that enforces: RBAC policy, idempotency, per-user/org rate limits, circuit breaker checks, structured audit logging, and retry/backoff.
- The guard sits around existing handlers—no business logic rewrite—so legacy commands gain consistent protection without breaking signatures.

## Multi-channel orchestration
- Expose the same automation actions across Telegram, email fallback, web UI buttons, and mobile mini-app flows through a central dispatcher (`AutomationService.execute(action, channel, context)`).
- Keeps behavior consistent across channels while honoring the same permissions, approval flows, and validation rules defined in F1–F4.

## Stuck job recovery and DLQ hygiene
- Add a periodic recovery worker that scans `BotJobOutbox` for stale `queued`/`processing` jobs; requeue safe tasks or move expired ones to the DLQ with a `BotEvent` explaining the decision.
- Publish clear DLQ ownership/SLA so human operators triage and reprocess failures instead of silent backlog growth.

## Conversation engine improvements
- Enrich `TelegramConversationState` (or equivalent) with `step`, `timeout`, and restart/cancel semantics to avoid drifting or orphaned flows.
- Guard each step with validation hooks and provide resumable paths so users can recover from errors without rerunning the entire flow.

## Automation policies by module
- Centralize rules in `automation_policies.yaml` (or config) for Orders, Inventory, Finance, CRM, Reports, Maintenance, and Banking.
- Examples: require reason codes for adjustments, enforce dual verification for payments, cap concurrent report jobs per user, and auto-release stale reservations.

## Validation order before execution
1. RBAC/permission check.
2. Policy evaluation (org/business rules).
3. Context validation (existence and state of orders/clients/stock).
4. Consistency guards (e.g., inventory invariants from F1/F2).
5. Predictive guardrails (e.g., pending action would deplete stock inside 48 hours).
6. User confirmation for high-risk actions.

## Bot observability & SLOs
- Add `/metrics/bot` (or extend existing metrics) to expose throughput, retry counts, stuck jobs, per-command latency/error rates, and conversation timeouts for Prometheus dashboards.
- Define bot SLOs aligned with F18 (e.g., <2s response for simple queries, <10s for critical actions, <0.5% automation failure) and tie error budgets to feature-flag rollbacks if exceeded.

## Bot separation and parallelism
- Classify commands in `BotCommandRegistry` by bot type and module (e.g., admin, reporting, ops, sales) to scope permissions and limit blast radius.
- Run parallel workers/queues per bot class where needed, leveraging F17’s priority queues to keep critical automations ahead of background chatter.

## Autonomous fallbacks
- For failures, provide deterministic fallbacks: explain RBAC denials, request missing context, offer repair flows (e.g., generate missing invoice), use alternate channels (email/UI) when Telegram or external APIs fail, and surface Sentry IDs for support.
- Keep human-in-the-loop for high-risk or ambiguous cases to avoid silent data corruption.

## Governance and safety checks
- Enforce RBAC from F4 in the dispatcher; require permissions for each command.
- Validate inputs before dispatch; reject malformed or untrusted payloads.
- Apply idempotency keys on every retry to avoid duplicate side effects.
- Keep DLQ under human ownership with operational SLAs for review and reprocessing.

## Rollout steps (additive)
1. Introduce validator and dispatcher wrappers; migrate existing handlers to run inside the sandbox.
2. Define contract modules and refactor bot handlers to call typed interfaces instead of direct model access.
3. Add DLQ table and governance jobs; wire Prometheus + Sentry instrumentation.
4. Harden conversation flows to use the bounded state machine; add tests for invalid transitions and recovery.
5. Gradually enforce throttling and RBAC on all bot entrypoints, including webhooks and scheduled bot jobs.

## Suggested tests
- Validation rejects malformed payloads and leaves no side effects.
- Idempotent retries do not duplicate ledger/order changes.
- Conversations cannot enter undefined states; recovery from errors returns to a safe step.
- DLQ captures failed jobs; `requeue_stuck_jobs` moves expired in-flight jobs appropriately.
- RBAC checks prevent unauthorized bot commands; authorized paths succeed.
- Metrics counters/gauges update on success and failure; Sentry traces include command name and duration.

## Operational questions to finalize
- Who owns DLQ triage and what is the SLA for reprocessing?
- How are long-running bot jobs handled (dedicated worker pool, timeouts)?
- What migration plan ensures legacy bot commands adopt typed contracts and RBAC without downtime?
