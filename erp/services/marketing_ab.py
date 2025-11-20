from __future__ import annotations

from decimal import Decimal
from random import random

from erp.models import MarketingABVariant


def pick_variant(org_id: int, campaign_id: int) -> MarketingABVariant | None:
    variants = (
        MarketingABVariant.query.filter_by(
            org_id=org_id, campaign_id=campaign_id, is_active=True
        ).all()
    )
    if not variants:
        return None

    total = sum(Decimal(variant.weight) for variant in variants)
    if total <= 0:
        return variants[0]

    threshold = Decimal(str(random())) * total
    cumulative = Decimal("0")
    for variant in variants:
        cumulative += Decimal(variant.weight)
        if threshold <= cumulative:
            return variant
    return variants[-1]
