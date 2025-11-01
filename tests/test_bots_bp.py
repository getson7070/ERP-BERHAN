def test_bots_slack_health(client):
    rv = client.get("/bots/slack/health")
    assert rv.status_code == 200


