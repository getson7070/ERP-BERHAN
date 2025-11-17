# Security Program Overview

## Supported Versions

ERP‑BERHAN is delivered as open‑source software.  The community provides best‑effort support on the most recent release branch and the current development branch.  Older versions do not receive regular updates.  Organisations running ERP‑BERHAN in production should maintain their own long‑term support policy and backport security fixes as needed.

## Reporting Vulnerabilities

If you discover a vulnerability or suspect a security issue in this codebase, please report it privately.  Do **not** create public issues describing the flaw.  Instead, send an email to the security team at `security@example.com` with a detailed description of the problem, steps to reproduce, and any potential impact.  We aim to acknowledge reports within **two business days** and provide a remediation timeline.  Critical vulnerabilities may result in public security advisories.

## Threat Model and Mitigations

ERP‑BERHAN operates in a multi‑tenant, web‑accessible environment.  Our security controls focus on confidentiality, integrity and availability of tenant data.  The following mitigations are implemented across the stack:

* **Row‑Level Security (RLS)**: Each database query must scope results to the current organisation via `resolve_org_id()`.  ORM models include `OrgScopedMixin` to enforce this pattern.
* **Rate Limiting**: A global rate‑limiting middleware protects against brute force and denial‑of‑service attacks.  Sensitive endpoints such as authentication and finance operations have stricter limits.
* **Content Security Policy (CSP)** and **Strict Transport Security (HSTS)**: These HTTP headers are configured by default to mitigate cross‑site scripting (XSS), clickjacking and other injection attacks.  All production deployments must enforce TLS with modern cipher suites.
* **Static Analysis and Dependency Scanning**: Continuous integration runs static code analysis and third‑party dependency checks.  Any high‑severity findings block merges.
* **Secrets Management**: Environment variables and secret management tools (e.g. Vault) store database credentials, API keys and PATs.  Secrets must never be committed to source control.

## Automated Agent Access and Controls

Codex/GPT assistants are authorised to create pull requests and propose changes.  These changes must be reviewed by a human maintainer before being merged.  To permit automated pushes during development:

1. Generate a Personal Access Token (PAT) with the minimum necessary scopes for a dedicated machine account.
2. Store this PAT as an encrypted secret (e.g. in GitHub Actions or a vault).  Do not embed it in code.
3. Update CI configuration to use the machine account when running automated tasks such as code generation.  Always require a human review before merging.
4. Document the scope and duration of any exception that allows direct pushes.  Remove these exceptions when releasing to production.

## TLS/mTLS Requirements

All client and server communications must be conducted over HTTPS.  Configure TLS with the following minimum recommendations:

| Control | Minimum Requirement |
| ------ | ------------------ |
| TLS version | 1.2 or higher |
| Key exchange | ECDHE |
| Certificate | Valid X.509 from a trusted CA |
| Mutual TLS (mTLS) | Required for service‑to‑service calls in the cluster |

mTLS ensures that internal services (e.g. finance API, CRM API) authenticate each other using certificates.  Certificates should be rotated regularly and stored securely.

## Email Authentication

Organisations deploying ERP‑BERHAN are encouraged to configure email authentication records to protect against spoofing:

* **SPF**: Publish an SPF record authorising your mail servers.
* **DKIM**: Sign outgoing mail using DKIM keys.  Rotate keys on a regular schedule.
* **DMARC**: Configure DMARC with a policy of at least `quarantine`.  Monitor aggregate reports to detect abuse.

## Incident Response

Upon receiving an incident report or detecting suspicious activity, follow the process documented in `docs/SRE_RUNBOOK.md`.  This includes validating the incident, containing the impact (revoking tokens or disabling endpoints), communicating with affected stakeholders, and conducting a post‑mortem.  Remediation steps must be tracked to completion.

## Development Exception for Testing

The ERP‑BERHAN project may permit a temporary relaxation of branch protection rules during development, allowing Codex/GPT to push directly to a feature or staging branch.  This exception must:

* Be limited in scope to non‑production data and infrastructure.
* Have a clear expiration date or be removed when the feature reaches maturity.
* Be disclosed in the pull request description and approved by at least one human maintainer.

This exception does **not** apply to the main branch.  All changes destined for production must undergo the standard pull request review process.

## Mapping to Compliance Frameworks

ERP‑BERHAN aligns its controls with recognised standards, including OWASP ASVS and NIST SP 800‑53.  The file `docs/security/asvs_traceability.md` contains a full matrix mapping controls to code, documentation and tests.  This matrix is generated automatically and verified in CI.  The project aims to achieve at least level 2 of ASVS for all components.

## Conclusion

By following the practices outlined above, developers and operators ensure that ERP‑BERHAN remains secure, resilient and compliant.  Security is a shared responsibility; all contributors must remain vigilant and proactive in identifying and mitigating risks.
