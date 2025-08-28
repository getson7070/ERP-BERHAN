# Implementation Backlog

This document consolidates the current Epic-level roadmap for ERP-BERHAN.
Each item lists the owner, priority, definition of done (DoD), and associated
validation tests.

## EPIC A — Security & Enforcement
- **A1. App-layer rate limiting + metrics** (P0)
  - DoD: Flask-Limiter enabled globally with `RATE_LIMIT_DEFAULT`; per-route
    limits on `/auth/login`, `/auth/token`, and `/api/graphql`. 429 responses
    exported via `rate_limit_rejections_total`.
  - Tests: pytest hits `/auth/login` until 429; k6 smoke triggers the limit.
- **A2. GraphQL depth/complexity enforcement** (P0)
  - DoD: middleware rejects queries over `GRAPHQL_MAX_DEPTH` or
    `GRAPHQL_MAX_COMPLEXITY`, emitting `graphql_rejects_total` and returning
    HTTP 400.
  - Tests: pytest for an over-deep query → 400 with snapshot body.
- **A3. Tamper-evident audit log** (P0)
  - DoD: `audit_logs` chain with `prev_hash`, `hash`, `created_at`; daily job
    scans and keeps `audit_chain_broken_total` at 0.
  - Tests: unit test builds a chain, corrupts a row, checker flags a break.
- **A4. Secret management & rotation playbook** (P1)
  - DoD: secrets pulled from vault/env; `JWT_SECRETS` rotated via
    `JWT_SECRET_ID`; runbook documented.
  - Tests: unit test validates old `kid` until TTL expiry.
- **A5. App lockout/backoff on failed logins** (P1)
  - DoD: progressive backoff and temporary lock after N failures with audit
    logging.
  - Tests: pytest simulates failures, verifies lock/unlock after cooldown.

## EPIC B — CI/CD & Quality Gates
- **B1. Full CI gates on push/PR** (P0)
  - DoD: CI runs ruff/flake8, black check, mypy, pytest+coverage (≥80%),
    pip-audit/Bandit, secret scan, Docker build + Trivy, kube-linter, and ZAP
    baseline. PRs must pass all.
- **B2. Coverage enforcement & HTML artifact** (P1)
  - DoD: coverage gate ≥80% with HTML report uploaded.
- **B3. Pre-commit hooks mirroring CI** (P2)
  - DoD: pre-commit config for ruff/black/mypy; docs updated.

## EPIC C — Data, Analytics & Freshness
- **C1. Faster KPI refresh (≤5 min) or incremental** (P0)
  - DoD: `kpi_sales` refreshed ≤5 min or incrementally; metric
    `kpi_mv_age_seconds` <300 under load.
- **C2. OLAP export path (Timescale/ClickHouse)** (P1)
  - DoD: nightly export of fact tables; BI queries run against OLAP store.
- **C3. Data retention & archival policy** (P1)
  - DoD: table-level retention windows; archival S3 bucket; PII masking.

## EPIC D — Platform & Scale
- **D1. PgBouncer + pool dashboards** (P1)
- **D2. Online migrations playbook** (P1)
- **D3. Idempotency & DLQ for Celery/Webhooks** (P1)

## EPIC E — Docker/K8s & Observability
- **E1. Harden Docker image** (P0)
- **E2. Probes, HPA & status page** (P1)

## EPIC F — UX Depth & Accessibility
- **F1. Unified notifications center** (P2)
- **F2. Kanban boards (jobs/tenders)** (P2)
- **F3. Inline edit & autosuggest** (P2)
- **F4. Accessibility (WCAG AA)** (P1)

## EPIC G — Mobile/PWA
- **G1. Quick-add actions & push notifications** (P2)
- **G2. Swipe actions (approve/reject)** (P3)

## EPIC H — Files & Storage
- **H1. S3 presigned uploads/downloads + AV scanning** (P2)

## EPIC I — Compliance & Governance
- **I1. Control matrix (ISO-27001 & Ethiopian regs)** (P1)
- **I2. Quarterly access recertification (automated)** (P1)

## EPIC J — E2E, Load & Chaos
- **J1. Playwright E2E smoke** (P1)
- **J2. k6/Locust soak & chaos** (P1)

## Issue Template
```
Title: [P0][EPIC A1] App-layer rate limiting + metrics
Context: Enforce per-user/IP/tenant limits to prevent abuse; expose 429s for observability.
Acceptance Criteria:
- Global default limit applied; per-route limits on login/token/GraphQL
- 429s recorded via rate_limit_rejections_total
- k6 smoke reliably triggers 429s
Automation: pytest for 429; k6 job in CI; export Prometheus counter as artifact
Owner: @security @platform • Milestone: M1 • Labels: security, ci-cd
Dependencies: Redis
```

