# Security & Load Testing

Run `scripts/security_scan.sh` for SAST and dependency checks.
Use `scripts/load_test.sh` or a preferred tool to validate performance at target concurrency.
GraphQL endpoints should be fuzzed with depth and complexity attacks.
`scripts/k6_rate_limit.js` provides a quick smoke test that triggers rate limits and verifies 429 responses under load.
`scripts/check_audit_chain.py` scans the audit log hash chain and reports any integrity breaks.

## Daily Audit Chain Verification

A scheduled GitHub Action (`audit-chain.yml`) runs every night and attaches the
latest verification log as a build artifact. Auditors can review the most
recent run under the workflow's artifacts list to confirm the chain remains
intact.
