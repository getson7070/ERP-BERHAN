import hashlib
import hmac
import json
import time


def _sign(secret: str, body: str, timestamp: str | None = None) -> tuple[str, str]:
    ts = timestamp or str(int(time.time()))
    basestring = f"v0:{ts}:{body}"
    signature = hmac.new(secret.encode("utf-8"), basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    return ts, f"v0={signature}"


def test_bots_slack_health(client):
    rv = client.get("/bots/slack/health")
    assert rv.status_code == 200
    assert rv.get_json()["signature_required"] is True


def test_slack_echo_rejects_missing_signature(client):
    payload = json.dumps({"text": "ping"})
    rv = client.post(
        "/bots/slack/echo",
        data=payload,
        content_type="application/json",
        headers={"X-Slack-Request-Timestamp": str(int(time.time()))},
    )
    assert rv.status_code == 401


def test_slack_echo_accepts_valid_signature(client):
    client.application.config["SLACK_SIGNING_SECRET"] = "secret"
    payload = json.dumps({"text": "ping"})
    timestamp, signature = _sign("secret", payload)
    rv = client.post(
        "/bots/slack/echo",
        data=payload,
        content_type="application/json",
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        },
    )
    assert rv.status_code == 200
    assert rv.get_json()["ok"] is True


