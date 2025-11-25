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
