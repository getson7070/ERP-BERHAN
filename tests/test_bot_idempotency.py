from erp import db
from erp.models import BotIdempotencyKey, BotJobOutbox
from erp.tasks.bot_worker import process_bot_job


def test_bot_idempotency_ignores_duplicate(app):
    with app.app_context():
        job = BotJobOutbox(
            org_id=1,
            bot_name="salesbot",
            chat_id="chat1",
            message_id="msg1",
            raw_text="inventory",
        )
        db.session.add(job)
        db.session.commit()

        db.session.add(
            BotIdempotencyKey(org_id=1, bot_name="salesbot", chat_id="chat1", message_id="msg1")
        )
        db.session.commit()

        result = process_bot_job(job.id)
        db.session.refresh(job)

        assert result["status"] == "duplicate_ignored"
        assert job.status == "done"
