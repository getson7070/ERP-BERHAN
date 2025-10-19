
# Phase 1 (Critical) — Changelog

- Add `erp/security.py` with strict headers (CSP, HSTS, X-Frame-Options, etc.)
- Add `erp/authz.py` with `require_permissions()` decorator for RBAC
- Add `erp/errors.py` with standardized JSON error payloads + request correlation
- Add `erp/observability.py` providing request IDs & structured logging (JSON to stdout)
- Add `erp/config.py` environment-first configuration & basic production validation
- Update `erp/__init__.py` app factory to wire logging, errors, security headers
- Add GitHub workflow `phase1-ci.yml` to start lint/type/test hygiene non-blocking
