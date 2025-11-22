import pytest

from erp import db
from erp.models import BotJobOutbox
from erp.tasks import bot_worker
from erp.tasks.bot_worker import process_bot_job


def test_bot_retry_increments(app, monkeypatch):
    with app.app_context():
        job = BotJobOutbox(
            org_id=1,
            bot_name="salesbot",
            chat_id="c1",
            message_id="m1",
            raw_text="approve order 1",
        )
        db.session.add(job)
        db.session.commit()

        def boom(*args, **kwargs):
            raise Exception("boom")

        monkeypatch.setattr(bot_worker, "dispatch", boom)

        with pytest.raises(Exception):
            process_bot_job(job.id)

        db.session.refresh(job)
        assert job.retry_count == 1
        assert job.status in {"queued", "failed"}
