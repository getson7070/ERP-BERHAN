# Privacy & Compliance Program

This roadmap aligns BERHAN ERP with ISO/IEC 27001 & 27701, SOC 2 Type II, and modern privacy regulations. It defines ownership, implementation phases, and the audit evidence captured in this repository.

## Strategic Objectives

1. **ISO/IEC 27001 & 27701** – Extend the Information Security Management System (ISMS) to cover privacy controls, link statements of applicability to risk registers, and conduct annual internal audits.
2. **SOC 2 Type II** – Maintain controls across the Trust Services Criteria (Security, Availability, Processing Integrity, Confidentiality, Privacy) with continuous evidence collection in CI pipelines.
3. **Regulatory Compliance** – Operationalize GDPR, CCPA/CPRA, and regional data protection laws by embedding privacy-by-design into feature delivery.

## Operating Model

- **Executive Sponsor:** COO – approves budget and staffing.
- **Data Protection Officer:** Privacy Officer (privacy@berhan.example) – oversees DPIA cadence, regulator communications, and privacy training.
- **Control Owners:** Engineering, Security, and Operations leads responsible for specific control families.
- **Evidence Repository:** Commit history, `docs/`, and automated CI artifacts form the primary control evidence.

## Implementation Phases

| Phase | Milestone | Target Quarter | Evidence |
| --- | --- | --- | --- |
| Foundation | ISMS scope, risk register, and asset inventory | Q1 | `docs/COMPLIANCE.md`, `docs/DATA_HANDLING_PROCEDURES.md` |
| Execution | Control rollout, staff training, DPIA coverage | Q2 | `/privacy` dashboard, DPIA artifacts, SRE/Postmortem docs |
| Assurance | Internal audit, SOC 2 readiness assessment | Q3 | `docs/PRIVACY_PROGRAM.md`, SOC 2 control matrix |
| Certification | External audit (ISO 27001/27701 + SOC 2 Type II) | Q4 | Signed SoA, audit reports |

## Control Framework Mapping

| Framework | Control Area | Repository Artifact |
| --- | --- | --- |
| ISO/IEC 27001 Annex A | A.5-A.18 | `docs/BERHAN_SOP_PACK.md`, `docs/security/*`, `docs/data_retention.md` |
| ISO/IEC 27701 | PIMS-5 to PIMS-12 | `docs/DATA_HANDLING_PROCEDURES.md`, `docs/DPIA_TEMPLATE.md` |
| SOC 2 TSC | CC2, CC6, CC7, CC8 | CI pipeline (`.github/workflows/ci.yml`), `SECURITY.md`, observability metrics |
| GDPR | Art. 5, 24, 30, 35 | `docs/DATA_HANDLING_PROCEDURES.md`, `docs/DPIA_TEMPLATE.md`, `docs/traceability.md` |
| CCPA/CPRA | §1798.100-1798.199 | DSAR runbook, privacy notices in UI |

## KPI Dashboard

Monitor these program metrics via `/privacy`:

- DPIA completion rate ≥ 95% for features that process PII.
- Average time to fulfill Data Subject Requests ≤ config target (default 30 days GDPR, 45 days CCPA).
- Upcoming audit tasks (internal/external) with owners and due dates.
- Privacy incident MTTR tracked in `docs/POSTMORTEM_TEMPLATE.md` follow-ups.

## Review Cadence

- **Weekly:** Privacy squad standup – review new features, open DPIAs, DSAR backlog.
- **Monthly:** Control owner sync – validate evidence, adjust risk treatment plans.
- **Quarterly:** Executive report – share compliance scorecard with leadership.

> Maintain this document as the single source of truth for certification status and control ownership. Link audit artifacts directly to git commits to preserve traceability.
