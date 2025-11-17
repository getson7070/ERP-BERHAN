# Agents Operating Manual

## Overview

This guide defines how automated and human agents should interact with the ERP‑BERHAN platform.  It replaces the prior agent documentation with a concise, standardised reference while retaining the same operational guidelines and safety requirements.  The intent is to make the expectations of agents transparent and enforceable across all modules of the application.

ERP‑BERHAN relies on a mixture of software components and automation, including GPT‑based code assistants (referred to hereafter as **Codex/GPT**) and human administrators.  Each agent type has distinct responsibilities and privileges.  This manual documents those roles, outlines security boundaries, and describes the approved mechanism for automated updates using personal access tokens (PATs).

## Roles and Responsibilities

### Human Contributors

Human contributors include developers, auditors, and system administrators.  They are responsible for reviewing pull requests, merging code into the main branch, responding to incident alerts, and approving or rejecting automated changes proposed by Codex/GPT.  Human contributors must:

* Enforce separation of duties and principle of least privilege when granting access to sensitive modules such as finance and HR.
* Perform code review on all changes to ensure they meet security, privacy and compliance requirements.
* Maintain awareness of the current threat landscape and update dependencies and configurations accordingly.

### Codex/GPT Assistants

Codex/GPT can generate code, write documentation and suggest configuration changes.  These assistants operate under human supervision and may not directly merge code into the main branch except under a controlled exception described below.  Codex/GPT must:

* Produce clearly scoped pull requests with descriptive titles and commit messages.
* Adhere to secure coding practices – avoid hard‑coded secrets, enforce input validation, and respect tenant boundaries by using helper functions like `resolve_org_id()`.
* Tag human reviewers for all changes and provide context for why the change is needed.

### Continuous Integration Service

The CI system builds and tests the application, runs static analysis, and executes security scans.  CI enforces branch protection rules, ensures all checks pass before a merge, and deploys to staging and production environments only when authorised by a release manager.

## Automated Updates Using PATs

ERP‑BERHAN recognises that certain routine changes (for example, regenerating translations or updating test data) may be performed automatically by Codex/GPT.  To facilitate this, a **dedicated machine account** should be created within your GitHub organisation.  The following guidelines apply:

1. **Create a unique PAT for the machine account** with the minimum scopes required (typically `repo` and `workflow`).  This token must never be shared with other services or stored in plain text.
2. **Store the token securely** using your organisation’s secret management system (for example, GitHub Actions secrets or a vault).  Do not embed the PAT in configuration files or commit history.
3. **Configure branch protections** so that automated pushes by the machine account require an approving review from a human maintainer.  This prevents unvetted changes from bypassing oversight.
4. **Label automated pull requests** clearly (for example, `bot:codex`) and assign the appropriate reviewers.
5. **Include clear commit messages** that describe the purpose of the change and reference relevant issues or tasks.

**Development Exception**: During development and testing, maintainers may temporarily relax branch protection rules to allow Codex/GPT to push directly to a non‑critical branch.  This exception must be documented in the pull request description, limited in scope and duration, and removed before production deployment.

## Safety and Privacy Controls

Agents must always follow the safety controls described in our security programme.  Key requirements include:

* **Data minimisation**: Collect and process only the data necessary for business operations.  Do not log personal or financial information unless required for audit.
* **Access control**: Use Role‑Based Access Control (RBAC) to restrict functions like approvals, financial postings, and HR operations to authorised roles.  Do not build logic that bypasses the `@login_required` decorator.
* **Tenant isolation**: Always call `resolve_org_id()` to scope queries and operations to the current organisation.  Never allow a user to access another tenant’s data.
* **Input validation**: Validate and sanitise all input from users and third‑party integrations.  Reject unexpected or malformed data with appropriate HTTP status codes.
* **Secrets management**: Use environment variables or secret vaults for API keys, database credentials and PATs.  Do not commit secrets into source control.

## Logging and Observability

Comprehensive audit logging is mandatory.  Agents must:

* Record all actions that modify state (e.g. creation of a finance entry, approval of a client registration, or deletion of a user) with timestamps and actor identifiers.
* Avoid logging sensitive fields such as passwords, authentication tokens, or personal financial data.
* Send logs to a centralised observability platform for real‑time monitoring and historical analysis.

## Incident Response and Recovery

In the event of a security incident or system failure, agents must coordinate with the site reliability engineering (SRE) team to contain and remediate issues.  Incident response guidelines are defined in `docs/SRE_RUNBOOK.md`.  Agents should:

* Immediately revoke compromised credentials or PATs and rotate them using the secret management process.
* Collect forensic logs and audit trails to understand root cause.
* Communicate findings in a post‑incident report and implement preventative measures.

## Conclusion

This manual standardises how humans and automated agents participate in the ERP‑BERHAN ecosystem.  By following these guidelines, the project ensures that automation accelerates development without compromising security, privacy or compliance.
