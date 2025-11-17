# Additional Security Controls

This document supplements `SECURITY.md` by summarising operational controls and guardrails that protect the ERP‑BERHAN platform.  It consolidates information previously scattered across multiple documents and aligns the project’s practices with recognised standards.

## Operational Security

* **Role‑Based Access Control (RBAC)**:  Policies defined in `policy/rbac.yml` determine which roles may perform actions such as creating finance entries, approving clients, or viewing HR data.  Always assign the least privilege role necessary.
* **Audit Trails**:  Every write operation emits an audit log containing the action performed, the user or service account, and a timestamp.  Logs must be immutable and retained according to the organisation’s data retention policy.
* **Secrets Rotation**:  Tokens, passwords and certificates should be rotated regularly.  Automated processes must trigger rotation at least every 90 days or upon suspicion of compromise.
* **Dependency Updates**:  The `docs/status.md` and `docs/roadmap.md` documents provide information on supported versions and upcoming deprecations.  Maintainers should schedule dependency updates quarterly.
* **Rate Limits**:  The file `.github/workflows/add-rate-limits.yml` includes automation to update rate limiting configuration.  Adjust thresholds as needed based on usage patterns to prevent abuse while avoiding false positives.

## Data Retention and Privacy

ERP‑BERHAN includes a `docs/data_retention.md` document that outlines default retention periods for various data categories.  Organisations must review and adjust these defaults based on regulatory requirements and internal policies.  Key principles include:

* **Minimise retention**:  Retain only the data necessary to fulfil legal and business obligations.
* **Secure disposal**:  At the end of the retention period, data should be securely deleted or anonymised so it cannot be reconstructed.
* **Transparency**:  Document retention schedules and communicate them to stakeholders.

## Incident Handling

The `docs/SRE_RUNBOOK.md` describes procedures for common incidents such as service outages, data breaches or suspicious log entries.  Highlights include:

1. **Detection** – Use monitoring tools and log alerts to detect anomalies.
2. **Response** – Follow an escalation matrix to notify on‑call engineers and security personnel.
3. **Containment** – Temporarily disable affected services or revoke credentials to stop the incident from spreading.
4. **Eradication and Recovery** – Apply patches, restore backups and test systems before bringing services back online.
5. **Post‑Mortem** – Conduct a blameless post‑mortem within 72 hours and document lessons learned.

## Compliance Mapping

To verify compliance with frameworks like OWASP ASVS, the project provides `docs/security/asvs_traceability.md`, which links each requirement to code, documentation and tests.  This mapping is automatically validated by a script in the CI pipeline.  Contributors adding new features should update the mapping to demonstrate coverage of relevant controls.

## References

For further information, consult the following documents:

* `SECURITY.md` – High‑level security programme
* `docs/SRE_RUNBOOK.md` – Incident response playbooks
* `docs/data_retention.md` – Data retention policies
* `docs/observability.md` – Logging and monitoring guidance
* `docs/epics_overview.md` – Roadmap and future improvements

These guardrails help ensure that ERP‑BERHAN remains secure, compliant and resilient as it evolves.
