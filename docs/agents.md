# Automated Agent (Codex) Guidelines

This document outlines policies for using automated agents – such as Codex-driven bots – to push updates directly to the `main` branch of the ERP‑BERHAN repository.

## Scope

Automated agents are non‑human services that run predefined tasks (dependency updates, documentation generation, refactoring, etc.). They operate under their own credentials and should adhere to project governance and security requirements.

## Authentication

- **Dedicated account:** create a dedicated GitHub machine user (e.g., `codex-bot`) separate from human contributors. Enable two‑factor authentication on this account.
- **Least privilege token:** generate a personal access token (PAT) scoped to the minimal permissions required (typically `repo` for writing to the repository). Avoid using administrator privileges.
- **Secure storage:** store the PAT in a secure secrets manager (e.g., AWS Secrets Manager or GitHub Actions secrets) and reference it in workflows via environment variables (e.g., `CODEX_TOKEN`). Never hard‑code tokens in source code.
- **Rotation & revocation:** rotate PATs every 90 days and immediately revoke tokens if there is any suspicion of compromise.

## Commit & Push Process

- **Attribution:** configure the environment variables `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` to reflect the automation account (e.g., `Codex Bot <codex-bot@example.com>`).
- **Conventional commits:** automated commits must follow the Conventional Commits style (e.g., `ci: update dependencies`, `docs: regenerate API spec`).
- **Direct pushes:** the `main` branch permits direct pushes from trusted automation accounts when pre‑configured quality gates (tests, linters, coverage checks) succeed. Workflows should fail and halt pushes if any gate fails.
- **Evidence:** Provide relevant CI job logs or commit messages when direct pushes, merges, or rebases occur so maintainers can audit the change.

 

- Maintain branch protection rules requiring status checks (unit tests, linting, security scans) to pass before commits are accepted from automation. Exempt only the trusted automation account if necessary.
- Use CODEOWNERS or reviewers to periodically audit automation activity to ensure compliance with repository standards.

## Security Considerations

- Automated agent code must not use `exec()` or dynamic evaluation of untrusted input.
- Do not embed secrets in code repositories; always pull secrets from the secrets manager at runtime.
- Monitor GitHub audit logs for the automation account; alert on any unusual activity.
- Document the responsibilities and escalation procedures for automation in the incident response playbooks.

### Establishing Connections & Push Mechanism

- **Git remote configuration:** To allow the automation agent to push directly to the `main` branch, configure the `origin` remote to use the personal access token (PAT) in the URL: `git remote set-url origin https://$CODEX_USERNAME:$CODEX_TOKEN@github.com/getson7070/ERP-BERHAN.git`. This keeps the credential scoped to the automation agent while enabling authenticated pushes.
By following these steps, the automation agent can establish a secure connection and push updates while respecting credential hygiene and traceability.

By following these guidelines, we ensure that Codex-driven bots can update the repository safely while maintaining high security and compliance standards.
