# Security & Load Testing

Run `scripts/security_scan.sh` for SAST and dependency checks.
Use `scripts/load_test.sh` or a preferred tool to validate performance at target concurrency.
GraphQL endpoints should be fuzzed with depth and complexity attacks.
`scripts/k6_rate_limit.js` provides a quick smoke test that triggers rate limits and verifies 429 responses under load.
