# Status

This page is updated by a scheduled GitHub Action and renders the SLO cards surfaced in the in-app `/status` dashboard.

### Current snapshot
- **Availability**: 99.96% (error budget consumed 12.5%)
- **Apdex**: 0.92 (T = 0.5s)
- **Queue backlog**: 8 jobs
- **Sales MV freshness**: 6m 22s

### Automation
- Nightly `audit-chain` runs compute and verify the hash chain over the audit log. See [run 987654321](https://github.com/getson7070/ERP-BERHAN/actions/runs/987654321) for the latest artifact.
- `publish-status.yml` writes JSON telemetry used by the status page cards (`.github/data/status.json`).
- Burn-rate alerts trigger PagerDuty and annotate the status board with incident references.

### References
- [SRE Incident Runbook](SRE_RUNBOOK.md)
- [Postmortem Template](POSTMORTEM_TEMPLATE.md)
- [Observability Strategy](observability.md)
- [Privacy & Compliance Program](PRIVACY_PROGRAM.md)
