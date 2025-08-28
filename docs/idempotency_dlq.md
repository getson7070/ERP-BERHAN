# Idempotency and Dead-Letter Queue

The system uses idempotency keys and a dead-letter queue to keep task
processing reliable and auditable.

## Idempotency Keys
- HTTP endpoints requiring exactly-once semantics include the
  `Idempotency-Key` header and are decorated with
  `erp.utils.idempotency_key_required`.
- Celery tasks may pass an `idempotency_key` argument and wrap the task with
  `erp.utils.task_idempotent` to prevent duplicate execution.

## Dead-Letter Queue
- Failures from Celery tasks are pushed to a Redis list named
  `dead_letter` via a task failure signal.
- `scripts/monitor_queue.py` can be extended to alert when the queue grows,
  helping operators investigate stuck tasks.
- Entries contain the task name, ID, error message, and arguments for
  post‑mortem analysis.
