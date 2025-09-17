# Incident Severity Levels

This document defines the severity classifications used in our incident response program. These levels help determine the urgency of response, communication cadence, and reporting obligations. Severity is assessed using impact on availability, integrity, confidentiality and user trust. Follow these definitions when triaging an incident.

## Severity 0 (Critical)
* **Definition:** A complete outage of core systems or confirmed data breach affecting a significant portion of customers or regulated data (e.g., PII/financial info). May involve compliance or legal obligations.
* **Response:** Immediate page of the Incident Commander and key stakeholders. Declare a major incident and mobilize full response team. Provide status updates at least every 30 minutes. Notify affected customers and regulators as required.

## Severity 1 (High)
* **Definition:** Partial outage or degradation of critical services impacting a large number of users, or high‑risk security vulnerability with credible exploitation. No confirmed data exfiltration.
* **Response:** Rapid escalation to on‑call engineers and Incident Commander. Provide updates at least every hour. Prepare customer communication if downtime exceeds SLAs.

## Severity 2 (Medium)
* **Definition:** Degradation of non‑critical functions or limited performance issues. Security incidents with low likelihood of data exposure. Workarounds may exist.
* **Response:** Acknowledge within 1 hour. Assign engineer to investigate. Provide updates every few hours until resolved.

## Severity 3 (Low)
* **Definition:** Minor bugs, documentation issues, or incidents with negligible customer impact. Could include false positives or misconfigurations discovered internally.
* **Response:** Address during normal business hours. No external communication unless requested. Track resolution in ticketing system and include in post‑incident review if necessary.

## Severity Review
Assessment of severity should be revisited as more information becomes available. Escalate or de‑escalate as necessary. Document all decisions and rationale in the incident ticket for auditability.
