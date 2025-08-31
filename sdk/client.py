"""Simple Python SDK for the ERP REST API."""

import requests


class ERPClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def ping(self):
        resp = requests.get(
            f"{self.base_url}/api/ping", headers=self._headers(), timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def get_orders(self):
        resp = requests.get(
            f"{self.base_url}/api/orders", headers=self._headers(), timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def send_integration_event(self, event: str, payload: dict) -> dict:
        """Send an event payload to the integration API."""
        resp = requests.post(
            f"{self.base_url}/api/integrations/events",
            json={"event": event, "payload": payload},
            headers=self._headers(),
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()

    def integrations_graphql(self, query: str) -> dict:
        """Execute a GraphQL query against the integration API."""
        resp = requests.post(
            f"{self.base_url}/api/integrations/graphql",
            json={"query": query},
            headers=self._headers(),
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
