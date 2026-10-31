"""RLRS-10: reminder planning and delivery with exactly-once semantics and retry.

The clock and the mail sender are injected, so tests need no real waiting and no SMTP.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, Iterable
from .types import ACTIVE, Reservation


class JobStatus(str, Enum):
    PENDING = "Pending"
    SENT = "Sent"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


@dataclass
class ReminderJob:
    reservation_id: int
    send_at: datetime
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    next_attempt_at: datetime | None = None

    def due_at(self) -> datetime:
        return self.next_attempt_at or self.send_at


def plan_reminder(res: Reservation, now: datetime, lead: timedelta = timedelta(hours=2)) -> ReminderJob | None:
    """Create a reminder job, or None if the slot has already started."""
    if res.interval.start <= now:
        return None
    return ReminderJob(res.id, max(res.interval.start - lead, now))


def cancel_jobs_for(job_list: Iterable[ReminderJob], reservation_ids: set[int]) -> int:
    n = 0
    for j in job_list:
        if j.reservation_id in reservation_ids and j.status == JobStatus.PENDING:
            j.status = JobStatus.CANCELLED
            n += 1
    return n


def process_due(jobs: Iterable[ReminderJob], reservations: Dict[int, Reservation], now: datetime,
                send: Callable[[Reservation], None], max_attempts: int = 3,
                backoff: timedelta = timedelta(minutes=5)) -> dict:
    """Send every due Pending job once. Safe to call repeatedly or after a restart:
    only Pending jobs are touched, and a Sent job is never sent again."""
    stats = {"sent": 0, "retry": 0, "failed": 0, "cancelled": 0}
    for job in jobs:
        if job.status != JobStatus.PENDING or job.due_at() > now:
            continue
        res = reservations.get(job.reservation_id)
        if res is None or res.status not in ACTIVE or res.interval.start <= now:
            job.status = JobStatus.CANCELLED  # cancelled/rejected/started: no reminder
            stats["cancelled"] += 1
            continue
        job.attempts += 1
        try:
            send(res)
        except Exception:
            if job.attempts >= max_attempts:
                job.status = JobStatus.FAILED
                stats["failed"] += 1
            else:
                job.next_attempt_at = now + backoff
                stats["retry"] += 1
        else:
            job.status = JobStatus.SENT
            stats["sent"] += 1
    return stats
