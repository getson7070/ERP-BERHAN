# Security & Load Testing

Run `scripts/security_scan.sh` for SAST and dependency checks.
Use `scripts/load_test.sh` or a preferred tool to validate performance at target concurrency.
GraphQL endpoints should be fuzzed with depth and complexity attacks.
`scripts/k6_rate_limit.js` provides a quick smoke test that triggers rate limits and verifies 429 responses under load.
`scripts/check_audit_chain.py` scans the audit log hash chain and reports any integrity breaks.

## Audit Chain Verification

A scheduled [GitHub Actions workflow](https://github.com/getson7070/ERP-BERHAN/actions/workflows/audit-chain.yml?query=branch%3Amain) runs nightly to execute `scripts/check_audit_chain.py` against the audit log. The job uploads an `audit-chain-report` artifact with the verification output so auditors can review recent integrity checks.
