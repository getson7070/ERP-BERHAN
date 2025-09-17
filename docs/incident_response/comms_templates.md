# Communication Templates

Effective communication is essential during incidents. This file provides reusable templates for notifying internal and external stakeholders at each stage of an incident, ensuring clear, accurate and consistent information.

## Internal notifications

Use this template to alert on‑call engineers, leadership and relevant teams when an incident is detected.

```
Subject: 🚨 [{{SEVERITY}}] Incident {{INCIDENT_ID}} – {{SYSTEM}} impacted

Team,

At {{DETECTION_TIME}} we detected an incident impacting {{SYSTEM}}. The current severity is {{SEVERITY}}.

Impact: {{IMPACT_DESCRIPTION}}

Actions taken: {{ACTIONS_TAKEN}}

Next update: We will provide an update by {{NEXT_UPDATE_TIME}} or sooner.

Please join the incident bridge: {{BRIDGE_LINK}}.

– Incident Commander
```

## External status update

Use this template to update customers or partners via status page or email. Keep messages factual and concise and avoid sharing sensitive details.

```
Subject: [{{SEVERITY}}] {{SERVICE}} Incident Update

We are aware of an issue affecting {{SERVICE}} beginning at {{DETECTION_TIME}}. Impacted customers may experience {{CUSTOMER_IMPACT}}.

Our team is actively investigating and working to restore full service as quickly as possible. We will provide the next update by {{NEXT_UPDATE_TIME}}.

We apologize for the inconvenience.
```

## Post‑incident closure

Once the incident has been resolved and impact mitigated, send a closure announcement summarizing what happened, the root cause and actions taken to prevent recurrence.

```
Subject: Resolved – Incident {{INCIDENT_ID}} {{SERVICE}} Restored

The incident impacting {{SERVICE}} has been fully resolved as of {{RESOLUTION_TIME}}. Root cause analysis identified {{ROOT_CAUSE}}, and we have taken the following remediation actions:

- {{REMEDIATION_ACTION1}}
- {{REMEDIATION_ACTION2}}

We will publish a detailed post‑mortem at {{POSTMORTEM_LINK}}.

Thank you for your patience.
```
