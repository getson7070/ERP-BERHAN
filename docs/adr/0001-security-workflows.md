# ADR 0001: Security Workflow Enhancements

## Status
Accepted

## Context
To strengthen the supply-chain security of the project, CI must verify that all commits are GPG-signed and that changes are reviewed by responsible parties defined in `CODEOWNERS`.

## Decision
1. Pin the Trivy GitHub Action to a specific commit SHA to avoid supply-chain attacks.
2. Introduce a CODEOWNERS validation workflow to ensure every change maps to an owning team.
3. Require commit signature verification in CI.

## Consequences
- CI fails if a commit is unsigned or CODEOWNERS entries are missing.
- Contributors must configure GPG keys and ensure CODEOWNERS entries are kept up to date.
- Workflow pinning prevents unexpected action updates.
