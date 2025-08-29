# Performance Testing

Use `scripts/seed_data.py` to populate large datasets before running load tests.

```
SEED_ITEMS=50000 SEED_USERS=5000 python scripts/seed_data.py
```

Run the Locust-based load test with adjustable parameters:

```
USERS=10000 RATE=500 DURATION=10m scripts/load_test.sh
```

Record throughput and error rates, then tune application and database settings accordingly.
