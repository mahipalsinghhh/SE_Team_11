"""RLRS-10: reminder jobs stored in the database and delivered by the background worker.

Same rules as rlrs_core.reminders, made durable:
* planned with rlrs_core.reminders.plan_reminder (default 2 hours before the slot);
* one job per reservation (unique column), so a reservation can never get two reminders;
* the worker claims a job (Pending -> Sending) inside a BEGIN IMMEDIATE transaction before it
  sends, so a second worker or a worker that runs twice can never send the same job again;
* jobs for cancelled/rejected/already-started reservations are cancelled, not sent;
* a failed send goes back to Pending with a back-off; after max attempts it is Failed.

Crash note: if the process dies after claiming but before recording the result, the job stays
in Sending and is not re-sent (at-most-once). That is deliberate: a duplicate reminder is worse
for users than a rare missed one, and Sending jobs are visible to staff via GET /api/reminders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Iterable

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from rlrs_core.reminders import plan_reminder
from rlrs_core.types import ACTIVE

from app import models as m
from app.engine import convert, notify

ACTIVE_VALUES = {s.value for s in ACTIVE}

PENDING, SENDING, SENT, FAILED, CANCELLED = "Pending", "Sending", "Sent", "Failed", "Cancelled"


def schedule_reminder(session: Session, reservation: m.Reservation, now: datetime,
                      lead: timedelta = timedelta(hours=2)) -> m.ReminderJob | None:
    """Create the reminder job for a new booking. Call inside the booking transaction
    (RLRS-6 calls this right after inserting the reservation). Idempotent."""
    existing = session.scalar(select(m.ReminderJob).where(m.ReminderJob.reservation_id == reservation.id))
    if existing is not None:
        return existing
    plan = plan_reminder(convert.reservation(reservation), now, lead)
    if plan is None:
        return None
    job = m.ReminderJob(reservation_id=reservation.id, send_at=plan.send_at, status=PENDING)
    session.add(job)
    return job


def cancel_reminders(session: Session, reservation_ids: Iterable[int]) -> int:
    """Cancel pending reminders for these reservations (cancel, reject, maintenance)."""
    ids = list(reservation_ids)
    if not ids:
        return 0
    result = session.execute(
        update(m.ReminderJob)
        .where(m.ReminderJob.reservation_id.in_(ids), m.ReminderJob.status == PENDING)
        .values(status=CANCELLED))
    return result.rowcount or 0


@dataclass
class _Claimed:
    job_id: int
    attempts: int
    to: str
    subject: str
    body: str


def _due(now: datetime):
    return or_(
        (m.ReminderJob.next_attempt_at.is_(None)) & (m.ReminderJob.send_at <= now),
        m.ReminderJob.next_attempt_at <= now,
    )


def _claim(sf: sessionmaker, job_id: int, now: datetime) -> _Claimed | str | None:
    with sf() as s, s.begin():
        job = s.get(m.ReminderJob, job_id)
        if job is None or job.status != PENDING or (job.next_attempt_at or job.send_at) > now:
            return None  # someone else already handled it
        res = s.get(m.Reservation, job.reservation_id)
        if res is None or res.status not in ACTIVE_VALUES or res.start_utc <= now:
            job.status = CANCELLED
            return "cancelled"
        job.status = SENDING
        job.attempts += 1
        subject, body = notify.reminder_email(res)
        return _Claimed(job.id, job.attempts, res.user.email, subject, body)


def run_reminders(sf: sessionmaker, now: datetime, send: Callable[[str, str, str], None],
                  max_attempts: int = 3, backoff: timedelta = timedelta(minutes=5)) -> dict:
    """One worker pass. Safe to run repeatedly, concurrently or after a restart."""
    stats = {"sent": 0, "retry": 0, "failed": 0, "cancelled": 0}
    with sf() as s:
        due_ids = list(s.scalars(select(m.ReminderJob.id)
                                 .where(m.ReminderJob.status == PENDING, _due(now))
                                 .order_by(m.ReminderJob.send_at)))
    for job_id in due_ids:
        claimed = _claim(sf, job_id, now)
        if claimed is None:
            continue
        if claimed == "cancelled":
            stats["cancelled"] += 1
            continue
        try:
            send(claimed.to, claimed.subject, claimed.body)
            error = None
        except Exception as exc:  # SMTP down, timeout, refused...
            error = f"{type(exc).__name__}: {exc}"[:300]
        with sf() as s, s.begin():
            job = s.get(m.ReminderJob, claimed.job_id)
            if error is None:
                job.status, job.sent_at, job.last_error = SENT, now, None
                stats["sent"] += 1
            elif claimed.attempts >= max_attempts:
                job.status, job.last_error = FAILED, error
                stats["failed"] += 1
            else:
                job.status, job.next_attempt_at, job.last_error = PENDING, now + backoff, error
                stats["retry"] += 1
    return stats
