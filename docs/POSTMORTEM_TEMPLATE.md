# Postmortem Template

Use this template for every Sev1/Sev2 incident within 24 hours of resolution.

## 1. Summary
- **Incident ID:**
- **Date/Time:**
- **Duration:**
- **Severity:**
- **Customer Impact:**
- **Detected By:**
- **NIST 800-53 Controls Engaged:**
- **Linked Evidence:** (e.g., logs/restore_drill.log entry, dashboards, comms templates)

## 2. Timeline
| Time (UTC) | Event | Owner |
| ---------- | ----- | ----- |
| 00:00 | Detection | |
| 00:05 | Incident acknowledged | |
| 00:15 | Initial update sent | |
| 00:30 | Mitigation deployed | |
| 01:00 | Service restored | |

## 3. Impact Assessment
- Affected products/features:
- SLA/SLO breach details:
- Error budget consumed:
- Customer communications sent:

## 4. Root Cause & Trigger
- Primary cause:
- Contributing factors:
- Triggering change/deployment:
- Why was the issue not detected earlier?

## 5. Detection & Response Review
- Alert coverage gaps:
- Time to acknowledge:
- Time to mitigate:
- What helped the team respond quickly?
- What slowed the response?

## 6. Corrective Actions
List concrete actions with owners and due dates.

| Action | Owner | Due Date | Status |
| ------ | ----- | -------- | ------ |
|  |  |  | ☐ Not started / ☐ In progress / ☐ Done |

## 7. Follow-up Tasks
- Add regression tests:
- Update runbooks/playbooks:
- Update monitoring/alerts:
- Required compliance notifications:
- Update NIST/ASVS traceability entry (Y/N, reference ID):

## 8. Lessons Learned
- What went well:
- What can be improved:
- Additional support needed:

## 9. Verification
- [ ] SLOs restored and monitored for 48 hours
- [ ] Follow-up tickets created in Jira
- [ ] Communication sent to stakeholders with summary
- [ ] Postmortem reviewed in SRE weekly review

## Appendix
- Related OTEL trace IDs:
- Links to dashboards/queries:
- Attachments/log bundles (include drill references, e.g., `logs/restore_drill.log` line numbers):
