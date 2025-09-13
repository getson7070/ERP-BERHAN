# Security Policy

This project follows the BERHAN Pharma Information Security Policy and implements controls consistent with ISO/IEC 27001. A mapping of ERP features to corporate policy pillars is maintained in [docs/corporate_policy_alignment.md](docs/corporate_policy_alignment.md). Planned hardening tasks and CI gate expansions are outlined in [docs/audit_roadmap.md](docs/audit_roadmap.md).

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅ |
| <0.1    | ❌ |

## Reporting a Vulnerability

Please email security@getsonpharma.com or open a private security advisory on GitHub. We will acknowledge receipt within 48 hours and provide status updates at least every five business days. Our goal is to release fixes within 14 days of confirmation.

## Triage, Disclosure & Fix

1. Incoming reports are triaged for severity and scope.
2. Valid issues receive a dedicated tracker with restricted access.
3. Patches are developed and reviewed under embargo.
4. Coordinated disclosure occurs after patches are released and, when applicable, a CVE is assigned.

Thank you for helping keep BERHAN PHARMA secure.

## Operational Security

- **Threat model**: multi-tenant ERP exposed to the internet; each organization is isolated via PostgreSQL row-level security.
- **RLS policy**: all tables carry an `org_id` column protected by an `org_rls` policy tied to `current_setting('erp.org_id')`.
- **Rate limits**: Flask-Limiter enforces sane defaults to mitigate abuse and brute-force attacks.
- **CSP/HSTS**: Flask-Talisman enforces a strict Content Security Policy with nonces on inline scripts and HTTP Strict Transport Security globally, with health checks opting out for probes.
- **Security tests**: CI runs static analysis, secret scanning, and RLS regression tests to catch common vulnerabilities early. All scanners (gitleaks, Bandit, pip-audit, Trivy, ZAP) fail the build on critical findings.
- **Secrets management**: all secrets are sourced from environment variables or the secret manager; no plaintext tokens are committed.
- **Dependency policy**: pinned requirements in `requirements.lock`; pip-audit and Trivy enforce zero high/medium vulnerabilities.
- **CSRF**: Flask-WTF provides global CSRF protection for form submissions.
