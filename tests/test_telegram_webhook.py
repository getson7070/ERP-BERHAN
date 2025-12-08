from datetime import datetime, timedelta, UTC
from http import HTTPStatus

import pytest

from erp.extensions import db
from erp.models import User, UserSession


@pytest.fixture(autouse=True)
def configure_telegram(app):
    app.config.update(
        TELEGRAM_WEBHOOK_REQUIRE_SECRET=True,
        TELEGRAM_WEBHOOK_SECRET="test-secret",
        TELEGRAM_REQUIRE_ACTIVE_SESSION=True,
        TELEGRAM_SESSION_MAX_AGE_SECONDS=7200,
    )
    return app


def _make_payload(chat_id: str, text: str = "/help"):
    return {"message": {"chat": {"id": chat_id}, "message_id": 1, "text": text}}


def test_webhook_requires_secret_when_configured(app, client):
    app.config["TELEGRAM_WEBHOOK_SECRET"] = None

    resp = client.post("/telegram/erpbot/webhook", json=_make_payload("111"))

    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert resp.get_json()["status"] == "misconfigured"


def test_webhook_blocks_without_active_session(app, client):
    app.config["TELEGRAM_WEBHOOK_SECRET"] = None
    with app.app_context():
        user = User(username="alice", email="alice@example.com", org_id=1, telegram_chat_id="111")
        user.password = "pass123!"
        db.session.add(user)
        db.session.commit()

    resp = client.post("/telegram/erpbot/webhook", json=_make_payload("111"))

    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.get_json()["status"] == "session_required"


def test_webhook_accepts_active_session(monkeypatch, app, client):
    class _StubTask:
        def delay(self, *_args, **_kwargs):
            return None

        def run(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr("erp.blueprints.telegram_webhook.process_bot_job", _StubTask())

    with app.app_context():
        user = User(
            username="bob",
            email="bob@example.com",
            org_id=1,
            telegram_chat_id="222",
        )
        user.password = "pass123!"
        db.session.add(user)
        db.session.flush()

        db.session.add(
            UserSession(
                org_id=1,
                user_id=user.id,
                session_id="sess-1",
                last_seen_at=datetime.now(UTC) - timedelta(minutes=5),
            )
        )
        db.session.commit()

    resp = client.post(
        "/telegram/erpbot/webhook",
        json=_make_payload("222"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["status"] == "queued"
