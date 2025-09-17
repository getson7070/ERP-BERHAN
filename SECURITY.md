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
- **Secrets management**: all secrets are sourced from environment variables or the secret manager; no plaintext tokens are committed outside of explicitly approved exceptions.
- **Temporary development exception**: while the product remains in active development and prior to the production launch sign-off, the security steering group may grant a time-boxed exception allowing ephemeral tokens (for example, Git personal access tokens) to reside in local tooling such as Git remote configurations. The following controls are mandatory:
  - approval recorded in the security exception register with an explicit expiry date tied to the production go-live decision;
  - tokens scoped to the minimum repository permissions and stored only in the local `.git/config` (never committed, shared, or pushed to remote state);
  - tokens rotated or revoked immediately after the authorized automation workflow completes and at least daily during the exception window;
  - audit trail documenting usage and confirming removal prior to production enablement.
- **Dependency policy**: pinned requirements in `requirements.lock`; pip-audit and Trivy enforce zero high/medium vulnerabilities.
- **CSRF**: Flask-WTF provides global CSRF protection for form submissions.

## Additional Security Policies

### Incident Response

For detailed incident response procedures including roles, communication templates, severity levels and triage flowcharts, refer to the [Incident Response Playbooks](docs/incident_response/README.md).

### TLS/mTLS Policy

- **TLS version**: Only TLS 1.2 or higher is permitted. Legacy protocols (TLS 1.1/1.0, SSL) are disabled.
- **Cipher suites**: Use modern cipher suites that provide forward secrecy (e.g., `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` and `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`).
- **HSTS**: HTTP Strict Transport Security is enabled with a max-age of at least one year (`max-age=31536000; includeSubDomains; preload`).
- **Mutual TLS (mTLS)**: Internal services and webhooks require mutual TLS authentication where feasible to ensure both client and server identity. Certificates are issued via the organization’s CA and rotated regularly.

### Email Authentication

To prevent email spoofing and improve deliverability, configure DNS records as follows:

- **SPF (Sender Policy Framework)**: Publish a SPF record (`v=spf1 include:spf.protection.outlook.com -all`) authorizing your sending IPs and reject unauthenticated sources.
- **DKIM (DomainKeys Identified Mail)**: Generate at least two 2048‑bit DKIM keys and add corresponding `TXT` records. Keys should be rotated annually.
- **DMARC (Domain-based Message Authentication, Reporting & Conformance)**: Enforce a reject policy with aggregated and forensic reporting:

  ```
  v=DMARC1; p=reject; rua=mailto:dmarc-aggregate@example.com; ruf=mailto:dmarc-forensics@example.com; pct=100
  ```

### Mapping to OWASP ASVS and NIST 800‑53

The controls implemented in this repository trace to the OWASP Application Security Verification Standard (ASVS) and NIST SP 800‑53 families. A high‑level mapping is provided below:

| Control Area | OWASP ASVS Section | NIST 800‑53 Control |
| --- | --- | --- |
| Access control / RBAC | V2 – Authentication and session management | AC‑2, AC‑3 |
| Input validation & encoding | V5 – Validation, sanitization and encoding | SI‑10 |
| Secrets management & encryption | V10 – Communications security | SC‑12, SC‑13 |
| Logging & monitoring | V10 – Logging and monitoring | AU‑2, AU‑6 |
| Software supply chain | V14 – Dependency management | SA‑12 |
| Incident response | V1 – Security architecture requirements | IR‑4, IR‑5 |

This mapping is maintained in `docs/security/system_security_updates.md` and will be refined as additional controls are implemented.
