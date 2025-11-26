# F16 — Intelligent Performance & Caching (Additive, Safe, High Impact)

## Goal
Make heavy operations fast, predictable, and cheap without changing business logic or conflicting with prior upgrades (21-task baseline, F1–F15). Focus on Inventory, Orders, and Reports while maintaining security, RBAC, CSRF, and data integrity.

## F16.1 Central Performance Policy
- Add a single config source (e.g., `PerformanceConfig` in `erp/config.py`) with TTLs, rate limits, and max page size.
- Expose via `current_app.config["PERF"]` so services and views consume consistent thresholds.

## F16.2 Read-Only Caching for Heavy Reads
- Implement a small Redis-backed helper (e.g., `erp/cache.py`) using SHA-256 of function signature/args as the cache key.
- Apply only to **read-heavy** service functions (inventory snapshots, order list summaries, report metadata). Avoid write paths.
- Use JSON serialization with safe defaults; fall back to the underlying function if Redis is unavailable.

## F16.3 Safe Cache Invalidation Hooks
- On stock movement commit (or equivalent domain event), delete affected cache namespaces (e.g., `cache:erp.inventory.services.get_stock_summary*`).
- Wire via SQLAlchemy events or existing domain-event handlers; ensure idempotent deletes.
- Worst case is cache miss → normal DB query; no data corruption risk.

## F16.4 Controlled Pagination & Max Page Size
- Add centralized pagination helper that clamps `page_size` to `1..MAX_PAGE_SIZE` and defaults to safe values.
- Use across orders/inventory/logs/reports endpoints to protect DB from unbounded queries.

## F16.5 N+1 Query Detection in CI
- Add a performance smoke test that counts SQL statements for critical endpoints (orders list, inventory list, reports) and enforces per-endpoint thresholds.
- Use SQLAlchemy `before_cursor_execute` listener during tests; integrate with CI without changing runtime behavior.

## F16.6 Background Generation for Heavy Reports
- Split report handling into request + async generation (Celery) + poll/download.
- Keep synchronous path for small reports but route through the same service; preserve backward compatibility.

## F16.7 Front-End Optimizations (Non-breaking)
- Client-side cache reference data; debounce searches; lazy-load heavy views; use skeleton loaders to improve perceived performance.
- No API changes required; purely UX/perceived performance improvements.

## Security, Stability, and Compatibility
- Caching is read-only and invalidated on domain events to avoid stale mutations.
- Pagination and rate limits mitigate abuse; RBAC/CSRF remain untouched.
- All changes are additive: no schema edits, no route renames, no business-logic changes.

## Expert Challenges to Address
- Measure before tuning (APM/metrics) to avoid guessing.
- Centralize cache invalidation ownership to prevent fragmentation.
- Avoid masking schema/index issues with caching; profile queries first.

## Suggested Next Layer
- F17 — Queue prioritization & task orchestration (ensure critical jobs do not wait behind low-priority tasks).
