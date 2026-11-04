"""Background worker: every RLRS_WORKER_INTERVAL_SECONDS, send due reminders and queued emails."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import Settings
from app.db import utcnow
from app.engine.outbox import flush_outbox
from app.engine.reminders import run_reminders

log = logging.getLogger("rlrs.worker")


def run_cycle(session_factory, mailer, settings: Settings, now: datetime | None = None) -> dict:
    now = now or utcnow()
    backoff = timedelta(minutes=settings.retry_backoff_minutes)
    result = {
        "reminders": run_reminders(session_factory, now, mailer.send, settings.max_send_attempts, backoff),
        "outbox": flush_outbox(session_factory, now, mailer.send, settings.max_send_attempts, backoff),
    }
    if any(result["reminders"].values()) or any(result["outbox"].values()):
        log.info("worker cycle %s", result)
    return result


def start_scheduler(session_factory, mailer, settings: Settings,
                    clock: Callable[[], datetime] = utcnow) -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(lambda: run_cycle(session_factory, mailer, settings, clock()),
                  "interval", seconds=settings.worker_interval_seconds,
                  id="rlrs-worker", max_instances=1, coalesce=True)
    sched.start()
    return sched
