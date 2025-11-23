"""Periodic metrics exporter for bot queues."""
from __future__ import annotations

from celery import shared_task

from erp.metrics import BOT_JOBS_FAILED, BOT_JOBS_QUEUED
from erp.models import BotJobOutbox


@shared_task(name="erp.tasks.bot.metrics_sweep")
def metrics_sweep(org_id: int):
    bots = (
        BotJobOutbox.query.filter_by(org_id=org_id)
        .with_entities(BotJobOutbox.bot_name)
        .distinct()
        .all()
    )
    for (bot_name,) in bots:
        queued = (
            BotJobOutbox.query.filter_by(
                org_id=org_id, bot_name=bot_name, status="queued"
            ).count()
        )
        failed = (
            BotJobOutbox.query.filter_by(
                org_id=org_id, bot_name=bot_name, status="failed"
            ).count()
        )
        BOT_JOBS_QUEUED.labels(str(org_id), bot_name).set(float(queued))
        BOT_JOBS_FAILED.labels(str(org_id), bot_name).set(float(failed))

    return {"bots": [b[0] for b in bots]}
