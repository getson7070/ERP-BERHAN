from erp.models import BotJobOutbox


def test_webhook_creates_job(client, db_session, resolve_org_id):
    org_id = resolve_org_id()
    payload = {
        "message": {
            "message_id": 10,
            "chat": {"id": 999},
            "text": "/inventory z50",
        }
    }

    resp = client.post("/telegram/testbot/webhook", json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "queued"

    job = BotJobOutbox.query.filter_by(org_id=org_id, chat_id="999").first()
    assert job is not None
    assert job.parsed_intent == "inventory_query"
    assert job.context_json.get("query") == "z50"
