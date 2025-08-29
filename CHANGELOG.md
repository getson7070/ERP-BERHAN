# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Pin Docker base image to `python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7` to ensure supply-chain integrity
- Harden Kubernetes deployment with pod `securityContext` and outbound-only NetworkPolicies

### UX
- Document accessibility and responsive design standards in `docs/ux_guidelines.md` with reference snapshots

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
