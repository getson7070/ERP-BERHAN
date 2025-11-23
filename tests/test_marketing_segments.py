from datetime import date, timedelta


class DummyClient:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_segment_rules_basic():
    from erp.services.marketing_segment_eval import matches_segment

    client = DummyClient(
        client_type="hospital",
        region="Addis Ababa",
        last_order_date=date.today() - timedelta(days=10),
        avg_monthly_spend=50_000,
    )

    rules = {
        "client_type": ["hospital"],
        "region": ["Addis Ababa"],
        "last_order_days_lte": 30,
        "avg_monthly_spend_gte": 30_000,
    }

    assert matches_segment(client, rules) is True

    rules["avg_monthly_spend_gte"] = 100_000
    assert matches_segment(client, rules) is False
