"""Simple Python SDK for the ERP REST API."""

import hashlib
import hmac
import json

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

    def send_signed_event(self, event: str, payload: dict, secret: str) -> dict:
        """Send a signed webhook event to the integration endpoint."""
        body = json.dumps({"event": event, "payload": payload})
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers = self._headers()
        headers["X-Signature"] = signature
        resp = requests.post(
            f"{self.base_url}/api/integrations/webhook",
            headers=headers,
            data=body,
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
