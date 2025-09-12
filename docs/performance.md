# Performance Testing

Use `scripts/seed_data.py` to populate large datasets before running load tests.

```
SEED_ITEMS=50000 SEED_USERS=5000 python scripts/seed_data.py
```

Run the Locust-based load test with adjustable parameters. The CI `perf.yml` workflow fails if the p95 latency exceeds **500 ms** or error rate surpasses **1%**.

```
USERS=10000 RATE=500 DURATION=10m scripts/load_test.sh
```

Record throughput and error rates, then tune application and database settings accordingly.

## WebSocket Fan-out

Live dashboards rely on WebSocket broadcasts. Monitor the number of connected
clients and the cost of sending updates to all of them. Consider sharding
broadcasts or using a message broker if fan-out becomes a bottleneck.
