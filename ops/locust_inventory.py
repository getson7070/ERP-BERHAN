"""Locust load generator for inventory adjustment throughput checks."""
from __future__ import annotations

import random
import uuid

from locust import HttpUser, between, task


class InventoryUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def stock_adjust(self):
        payload = {
            "item_id": str(uuid.uuid4()),
            "warehouse_id": str(uuid.uuid4()),
            "qty_delta": random.choice([1, -1, 5, -2]),
            "tx_type": "adjust",
            "idempotency_key": str(uuid.uuid4()),
        }
        self.client.post("/api/inventory/adjust", json=payload)

    @task(1)
    def expiring_lots(self):
        self.client.get("/api/inventory/lots/expiring")
