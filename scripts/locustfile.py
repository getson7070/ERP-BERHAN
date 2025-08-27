from locust import HttpUser, task, between

class PharmaUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def create_invoice(self):
        payload = {"number": "INV-0001", "total": "0.00"}
        self.client.post("/invoice", json=payload)
