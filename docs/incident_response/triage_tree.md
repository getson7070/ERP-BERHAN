# Incident Triage Tree

This document outlines the decision flow used during incident triage. It helps responders quickly determine severity, assign roles, and execute appropriate mitigation actions. Follow this tree to ensure consistent handling of security and reliability incidents.

1. **Detection and Verification**
   - Confirm the alert or report is legitimate (e.g., via monitoring, user reports, or automated tooling).
   - Gather initial evidence: logs, error messages, traces, and screenshots.
   - Determine if the issue affects availability, integrity, confidentiality or safety.

2. **Classify Impact**
   - **System Scope:** Is the issue isolated to a single service or is it widespread across multiple services or regions?
   - **User Impact:** Estimate how many customers/users are affected and whether sensitive data is at risk.
   - **Business Impact:** Assess regulatory or financial implications, contractual SLAs and critical business processes.

3. **Assign Severity Level**
   - Use the definitions in `severity_levels.md` to select the appropriate severity (0–3).
   - If unsure, start at the higher severity and de‑escalate once more information is available.

4. **Mobilize Response Team**
   - Page the Incident Commander (IC) and other on‑call engineers commensurate with the severity.
   - Assign a Scribe to document the timeline and actions taken.
   - Engage Subject Matter Experts (SMEs) based on the affected components (e.g., database, networking, security).

5. **Initial Mitigation**
   - Contain the issue: isolate affected services, enable failover, or revoke compromised credentials.
   - Communicate interim status updates to stakeholders and, if severity ≥ 1, prepare customer communications.

6. **Investigate and Diagnose**
   - Identify the root cause using logs, traces, metrics and, if applicable, anomaly detection.
   - Evaluate whether the incident triggers any NIST 800‑53 controls (e.g., IR‑4, IR‑6) and document evidence accordingly.

7. **Resolution and Recovery**
   - Apply fixes, patches, or configuration changes to restore normal operations.
   - Monitor post‑fix metrics and logs to ensure the issue is resolved.
   - Update the incident ticket with resolution steps and verify that services meet defined SLOs.

8. **Post‑Incident Activities**
   - Perform a formal post‑mortem within 72 hours. Include root cause analysis, timeline, impact assessment, and lessons learned.
   - Record evidence of NIST 800‑53 incident handling (IR controls) and map the incident to OWASP ASVS requirements.
   - Create or update runbooks and playbooks to prevent recurrence.

This triage tree complements the severity classifications and ensures incidents are managed consistently and transparently. Deviations should be documented and justified during the post‑mortem.
