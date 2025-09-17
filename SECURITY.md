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
- **ASVS traceability**: run `python scripts/verify_asvs.py` locally before opening a pull request to ensure every OWASP ASVS requirement maps to code, tests, or runbooks. The CI pipeline runs the same check after blueprint validation.
- **Secrets management**: all secrets are sourced from environment variables or the secret manager; no plaintext tokens are committed outside of explicitly approved exceptions.
- **Temporary development exception**: while the product remains in active development and prior to the production launch sign-off, the security steering group may grant a time-boxed exception allowing ephemeral tokens (for example, Git personal access tokens) to reside in local tooling such as Git remote configurations. The following controls are mandatory:
  - approval recorded in the security exception register with an explicit expiry date tied to the production go-live decision;
  - tokens scoped to the minimum repository permissions and stored only in the local `.git/config` (never committed, shared, or pushed to remote state);
  - tokens rotated or revoked immediately after the authorized automation workflow completes and at least daily during the exception window;
  - audit trail documenting usage and confirming removal prior to production enablement.
- **Dependency policy**: pinned requirements in `requirements.lock`; pip-audit and Trivy enforce zero high/medium vulnerabilities.
- **CSRF**: Flask-WTF provides global CSRF protection for form submissions.
