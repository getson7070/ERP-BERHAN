# Compliance Module

This module introduces primitives for FDA 21 CFR Part 11, GMP workflows, and the expanded privacy/compliance program.

## Electronic Signatures
- Captures user intent and timestamp.
- Generates a tamper-evident hash chain for each signature.

## Electronic Batch Records
- Stores lot numbers and manufacturing descriptions.
- Links to non-conformance records for quality events.

## Non-Conformance & Privacy Tracking
- Records deviations with open/closed status.
- Maintains privacy impact assessments via the `privacy_impact_assessments` table.
- Surface privacy KPIs, audit readiness, and DPIA coverage in the `/privacy` dashboard.

Endpoints are exposed under `/api/compliance/*` and require authenticated users with the `auditor` role.

### Certification Roadmap

| Framework | Status | Artifact |
| --- | --- | --- |
| ISO/IEC 27001 & 27701 | In-progress | `docs/PRIVACY_PROGRAM.md`, `SECURITY.md` |
| SOC 2 Type II | In-progress | `docs/PRIVACY_PROGRAM.md`, `.github/workflows/ci.yml` |
| GDPR / CCPA | Operational | `docs/DATA_HANDLING_PROCEDURES.md`, `docs/DPIA_TEMPLATE.md`, `docs/DSAR_RUNBOOK.md` |

Refer to [BERHAN_SOP_PACK.md](BERHAN_SOP_PACK.md) for the master SOP template and policy mappings, and consult the [Code of Conduct](../CODE_OF_CONDUCT.md) for overarching corporate requirements.
