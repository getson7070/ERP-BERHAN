def test_bot_job_context_forwarded(app, monkeypatch):
    from erp import db
    from erp.bots.dispatcher import COMMANDS
    from erp.models import BotJobOutbox, Role, User
    from erp.tasks.bot_worker import process_bot_job

    captured = {}

    # Replace the approve handler so we can assert the inbound context is flat
    # (entity_type/entity_id) instead of nested under "context".
    COMMANDS["approve_action"].handler = lambda ctx: captured.setdefault("ctx", ctx) or {"text": "ok"}
    COMMANDS["approve_action"].required_role = None
    monkeypatch.setattr("erp.bots.dispatcher.resolve_org_id", lambda: 1)

    with app.app_context():
        role = Role.query.filter_by(name="admin").first()
        if not role:
            role = Role(name="admin")
            db.session.add(role)
            db.session.commit()

        user = User(
            org_id=1,
            username="botctx_admin",
            email="botctx_admin@example.test",
        )
        user.password = "testpass123"
        user.telegram_chat_id = "chat123"
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        job = BotJobOutbox(
            org_id=1,
            bot_name="erpbot",
            chat_id="chat123",
            message_id="99",
            raw_text="/approve ORDER 321",
            parsed_intent="approve_action",
            context_json={"entity_type": "ORDER", "entity_id": 321},
        )
        db.session.add(job)
        db.session.commit()

        monkeypatch.setattr(
            "erp.tasks.bot_worker.send_telegram_message",
            lambda *_, **__: {"ok": True},
        )
        monkeypatch.setattr(
            "erp.tasks.bot_worker._resolve_user",
            lambda _job: db.session.get(User, user_id),
        )
        result = process_bot_job.run(job.id)
        db.session.refresh(job)

        assert result["status"] == "ok"
        assert job.status == "done"
        assert captured["ctx"]["entity_type"] == "ORDER"
        assert captured["ctx"]["entity_id"] == 321
        assert captured["ctx"]["user"].id == user_id
