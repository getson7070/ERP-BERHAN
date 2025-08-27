# Chaos and Soak Testing

- Run long-duration load tests via `scripts/soak_test.sh` before releases.
- Periodically execute `scripts/chaos_worker.sh` to ensure workers respawn and
  queues drain without manual intervention.
- Record outcomes and adjust alerting thresholds based on observations.
