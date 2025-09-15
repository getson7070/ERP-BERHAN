# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Pin Docker base image to `python:3.11-slim@sha256:1d6131b5d479888b43200645e03a78443c7157efbdb730e6b48129740727c312` to ensure supply-chain integrity
- Harden Kubernetes deployment with pod `securityContext` and outbound-only NetworkPolicies
- Recreate row-level security policies using `erp.org_id` to enforce tenant isolation
- Refactor authentication and order routes to use parameterised SQL queries for injection safety and cross-database support
- Docker Compose connections to PostgreSQL now require TLS (`sslmode=require`)

### UX
- Document accessibility and responsive design standards in `docs/ux_guidelines.md` with reference snapshots
- Break long template lines and add SRI/crossorigin attributes for CDN assets
- Service worker securely reattaches fresh auth tokens when replaying background-sync requests
- Dynamically revealed inventory expiration field now toggles `aria` attributes for screen-reader support

### Ops
- Add missing Alembic revision for data lineage table to ensure migration chain completeness
- Container health checks reference `/healthz` endpoint for consistent probe configuration
- Linearized Alembic migration history to eliminate multiple heads
- Database migrations are executed via `scripts/run_migrations.sh` prior to starting application services
- Deterministic builds install dependencies from `requirements.lock` and docs outline `scripts/setup_postgres.sh` for local provisioning
- dockerfile sets a default `CMD` to run migrations and launch Gunicorn on `0.0.0.0:8080` so App Runner can pass health checks
- Skip Redis check in `/healthz` when no broker URL is configured to prevent false health probe failures
- Package test utilities to avoid mypy duplicate-module errors
- Playwright tests skip when required browser dependencies are missing to avoid CI failures
- Composite indexes added on `(status, org_id)` for `orders`, `maintenance`, and `tenders` tables to accelerate dashboards
- Analytics reminders log via structured logging instead of `print`
- Standalone `init_db.py` bootstraps core schema, seeds a default organisation and Admin role, and applies RLS policies
- Enforce branch coverage with mutation testing and commit message linting for Conventional Commits
- Introduced `scripts/index_audit.py` and `DATABASE.md` to track indexing health and RPO/RTO targets

### Added
- Gunicorn now respects `WEB_CONCURRENCY`, `GUNICORN_THREADS`, and `GUNICORN_TIMEOUT` environment variables and exports per-worker metrics.
- GraphQL depth and complexity are validated using an AST-based analyzer instead of string heuristics.
- Kubernetes manifests define resource requests/limits with an HPA driven by latency and queue lag metrics.
- Coverage configuration includes core modules with a higher failure threshold to surface untested code.
- Expose `/health` and `/healthz` endpoints with lightweight database and Redis checks for container probes
- Row‑level security policies recreated to read the tenant ID from `current_setting('erp.org_id')`
- Audit logging, data retention, analytics tasks, Telegram bot, orders, and authentication routes now use parameterized SQL for cross‑database compatibility
- CDN assets include SRI hashes with `crossorigin` attributes and the service worker reattaches fresh auth tokens
- Application startup skips role seeding when the `roles` table is missing, preventing migration failures on fresh databases

## [0.1.0] - 2025-08-28
- Add PgBouncer deployment manifests
- Track cache hit rate with Prometheus gauge
- Extend CI with ruff, coverage gate, security scans, ZAP, and accessibility audit
- Document control matrix and access recertification exports
- Provide feedback endpoint and customizable dashboard route checks
- Refine coverage configuration so targeted tests meet the 80% threshold
- Enforce GraphQL depth and complexity limits with `graphql_rejects_total` metric
- Add tamper‑evident audit log chain checker emitting `audit_chain_broken_total`
- Document JWT secret rotation runbook and verify old keys until expiry
- Implement progressive login backoff with temporary account lock and audit logging
