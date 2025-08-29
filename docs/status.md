# Status

This page is updated by a scheduled GitHub Action and exposes recent operational metrics.

- **p95 API latency**: 120ms
- **Queue lag**: 3
- **Materialized view freshness**: 45s
- **Rate-limit 429s**: 2

## How the audit chain is verified
Nightly `audit-chain` runs compute and verify a checksum over the audit log. See [run 987654321](https://github.com/getson7070/ERP-BERHAN/actions/runs/987654321) for details.

The action also publishes a JSON artifact alongside this file for external dashboards.
