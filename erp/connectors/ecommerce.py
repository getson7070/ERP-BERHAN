import requests


def fetch_products(endpoint: str):
    """Retrieve products from an external e-commerce API."""
    response = requests.get(endpoint, timeout=5)
    response.raise_for_status()
    return response.json()
