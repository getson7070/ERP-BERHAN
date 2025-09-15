# SRE Incident Runbook

## Purpose
Provide an actionable playbook for detecting, triaging, and resolving production incidents while protecting the customer experience, safeguarding data, and preserving regulatory obligations.

## Service-Level Objectives
| SLO | Target | Window | Error Budget |
| --- | ------ | ------ | ------------ |
| API availability | ≥ 99.9% | 30 days | 43m 12s per window |
| Apdex (T = 0.5s) | ≥ 0.85 | rolling | N/A |
| Celery backlog | ≤ 50 jobs (warning ≥ 75, breach ≥ 100) | continuous | N/A |
| Sales MV freshness | ≤ 15 minutes (warning 20, breach 30) | continuous | N/A |

Escalate immediately if the burn rate exceeds **2×** for 15 consecutive minutes or any SLO breaches its threshold.

## Roles & Responsibilities
- **Incident Commander (IC):** coordinates triage, owns communication cadence, ensures timelines are captured.
- **Operations Engineer (Ops):** executes mitigations, validates infrastructure health, coordinates with cloud providers.
- **Comms Lead:** manages stakeholder messaging (internal/external) using pre-approved templates.
- **Scribe:** documents actions and decisions, opens the postmortem issue, tracks follow-ups.

## Detection & Paging
1. Alerts originate from Prometheus, OpenTelemetry exporters, or synthetic monitors.
2. PagerDuty routing policies target the on-call rotation. Secondary notification via Slack `#incidents` channel.
3. If automated paging fails, escalate manually by calling the on-call phone tree within 5 minutes.

## First 15 Minutes Checklist
1. **Acknowledge alert** within 5 minutes.
2. **Establish IC** and open a dedicated Slack/Teams channel (`inc-<date>-<summary>`).
3. **Assess impact:** confirm affected regions/customers, collect baseline metrics (Apdex, 5xx rate, queue backlog).
4. **Stabilize:** roll back recent deployments or enable feature flags if needed. Document decisions in the channel.
5. **Communicate:** send initial incident notification using the `docs/templates/incident-comms.md` template.

## Mitigation Playbooks
### Elevated 5xx / Availability breach
- Check recent deploys; if within 30 minutes, initiate automated rollback (ArgoCD `rollout undo`).
- Verify database health (connections, replication lag). Failover to read replica if primary degraded.
- Capture OTEL trace samples for the affected endpoints and correlate with logs via trace/span IDs.

### Queue backlog > 100 jobs
- Scale Celery workers (`kubectl scale deployment celery-workers --replicas=<n>`).
- Inspect blocked tasks with `scripts/index_audit.py` for locking or missing indexes.
- Flush poison messages to DLQ (`redis-cli lrange dead_letter 0 -1`).

### Sales MV stale > 30 minutes
- Trigger manual refresh `flask cli run analytics.refresh_kpis`.
- Inspect OLAP export pipeline for errors, review CloudWatch logs.

## Communication Cadence
- Initial update: ≤ 15 minutes from detection.
- Subsequent updates: every 30 minutes (higher if impact remains high).
- Customer notification: coordinate with Comms Lead once root cause identified or mitigation underway.

## Recovery Validation
- Confirm SLOs trending toward targets (availability ≥ 99.9%, Apdex ≥ 0.85).
- Ensure queue backlog returns below 50 and stays there for 10 minutes.
- Run smoke tests (login, order submission, analytics export).
- Remove feature flags or mitigations after verifying stability.

## After Action
1. Close the incident channel with final status and link to postmortem issue.
2. Open a postmortem using [docs/POSTMORTEM_TEMPLATE.md](POSTMORTEM_TEMPLATE.md) within 24 hours.
3. Create follow-up tasks in Jira (`Reliability` project) and assign owners.
4. Schedule remediation reviews during the weekly SRE sync and track to completion.

## Audit & Compliance
- Preserve OTEL trace IDs and logs for at least 90 days.
- Store incident timelines in the evidence repository (`s3://erp-berhan-irm/incidents`).
- Coordinate with compliance for any SLA breaches or regulatory reporting requirements.

## References
- [Observability guide](observability.md)
- [Disaster recovery plan](dr_plan.md)
- [Status page playbook](status.md)
