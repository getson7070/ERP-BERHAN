from __future__ import annotations

from datetime import date


def matches_segment(client, rules: dict) -> bool:
    """Evaluate a lightweight segment rule set against a client object."""
    if "client_type" in rules:
        allowed_types = set(rules["client_type"])
        if getattr(client, "client_type", None) not in allowed_types:
            return False

    if "region" in rules:
        allowed_regions = set(rules["region"])
        if getattr(client, "region", None) not in allowed_regions:
            return False

    if "last_order_days_lte" in rules:
        max_days = int(rules["last_order_days_lte"])
        last_order_date = getattr(client, "last_order_date", None)
        if not last_order_date:
            return False
        if (date.today() - last_order_date).days > max_days:
            return False

    if "avg_monthly_spend_gte" in rules:
        minimum = float(rules["avg_monthly_spend_gte"])
        spend = float(getattr(client, "avg_monthly_spend", 0))
        if spend < minimum:
            return False

    return True
