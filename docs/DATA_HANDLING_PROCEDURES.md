# GDPR & CCPA Data-Handling Procedures

This playbook formalizes how BERHAN ERP processes personal data to maintain continuous compliance with GDPR, CCPA/CPRA, and related privacy regimes.

## 1. Governance & Roles

- **Data Protection Officer (DPO):** Privacy Officer (default: privacy@berhan.example). Owns policy updates, breach notifications, and regulator correspondence.
- **Privacy Squad:** Cross-functional leads from Security, Legal, Engineering, and Product. Meets bi-weekly to review backlog items that touch PII or sensitive data.
- **Service Owners:** Module maintainers ensure new features trigger DPIA reviews and follow approved retention/erasure workflows.

## 2. Data Inventory & Classification

1. Maintain the system-of-record in `docs/data_retention.md` describing every table that stores or references personal data.
2. Tag models with privacy metadata (e.g., `anonymized`, `retain_until`) and capture lineage in the `data_lineage` table.
3. Update the privacy inventory whenever new data sources or third-party processors are introduced.

## 3. Lawful Basis & Consent

- Default lawful basis: **Contractual Necessity** for core ERP processing and **Legitimate Interest** for analytics.
- Capture explicit consent for optional analytics or communications; store consent receipts via the `electronic_signatures` table.
- Provide granular opt-out toggles in the UI for marketing communications and optional analytics exporters.

## 4. Data Subject Rights Workflow

| Request Type | Regulation | SLA | Handler |
| --- | --- | --- | --- |
| Access / Portability | GDPR Art. 15 & 20 | 30 days | Privacy Squad |
| Deletion / Erasure | GDPR Art. 17 | 30 days | Data Engineering |
| Do Not Sell / Share | CCPA §1798.120 | 15 days | Privacy Squad |
| Opt-out of Profiling | GDPR Art. 22 | 30 days | Product & ML Team |

1. Requests enter via the self-service privacy portal (planned) or support ticket.
2. Log all cases in the `privacy_impact_assessments` table with `status="dsr-open"` until completed.
3. Validate requestor identity via existing MFA or notarized letter when digital methods fail.
4. Produce exports using anonymization helpers before delivery and document completions in the audit log.

## 5. Data Minimization & Retention

- Follow deletion schedules in `docs/data_retention.md` and ensure `retain_until` is enforced in cron jobs.
- For analytics, strip direct identifiers (names, email, phone) before sending to downstream processors.
- Use field-level encryption for sensitive attributes (biometrics, geolocation) when storage in PostgreSQL is unavoidable.

## 6. International Transfers

- Default hosting region: `eu-west-1` (configurable via `PRIVACY_DATA_RESIDENCY`).
- Use Standard Contractual Clauses (SCCs) and supplementary controls (encryption, access logging) for transfers outside the EU/EEA.
- Maintain the subprocessors list in `docs/COMPLIANCE.md` and update contracts annually.

## 7. Incident Response & Breach Notification

1. Activate the SRE incident playbook in `docs/SRE_RUNBOOK.md` and notify the DPO immediately.
2. Assess risk to individuals; if high, notify the supervisory authority within 72 hours (GDPR Art. 33) and affected subjects without undue delay (Art. 34).
3. Record the breach timeline, remediation, and evidence in the postmortem template.

## 8. Continuous Monitoring

- Run quarterly privacy control audits using `scripts/privacy_gap_analysis.py` (planned) to verify DPIA coverage, request SLAs, and access logging.
- Track metrics for DPIA completion time, data subject request SLAs, and privacy incident MTTR in the observability dashboard.
- Revisit these procedures whenever regulations change or new data processing initiatives commence.

> **Tip:** Link completed DPIAs and DSR cases directly from the `/privacy` dashboard so product managers can verify compliance posture before launching features.
