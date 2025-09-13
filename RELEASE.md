# Release Policy

Releases follow a weekly PATCH, monthly MINOR, and quarterly MAJOR schedule. Each release is gated on:

- All CI checks green with coverage ≥90%
- Zero high or medium vulnerabilities in CodeQL, Bandit, Gitleaks, pip-audit, and Trivy
- Successful canary deployment meeting p95 latency and error rate SLOs

Rollback procedures and deployment logs must be attached for every release.
