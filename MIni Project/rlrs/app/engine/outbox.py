"""Transactional email outbox: queue inside the business transaction, deliver after commit.

Used for notifications that must be atomic with a data change (maintenance cancellations,
and RLRS-9 confirmation emails can reuse it). Same claim/retry rules as reminders.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from app import models as m

PENDING, SENDING, SENT, FAILED = "Pending", "Sending", "Sent", "Failed"


def queue_email(session: Session, to: str, subject: str, body: str, now: datetime) -> m.OutboxEmail:
    mail = m.OutboxEmail(to=to, subject=subject, body=body, status=PENDING, created_at=now)
    session.add(mail)
    return mail


def flush_outbox(sf: sessionmaker, now: datetime, send: Callable[[str, str, str], None],
                 max_attempts: int = 3, backoff: timedelta = timedelta(minutes=5)) -> dict:
    stats = {"sent": 0, "retry": 0, "failed": 0}
    with sf() as s:
        ids = list(s.scalars(select(m.OutboxEmail.id).where(
            m.OutboxEmail.status == PENDING,
            or_(m.OutboxEmail.next_attempt_at.is_(None), m.OutboxEmail.next_attempt_at <= now))
            .order_by(m.OutboxEmail.id)))
    for mail_id in ids:
        with sf() as s, s.begin():
            mail = s.get(m.OutboxEmail, mail_id)
            if mail is None or mail.status != PENDING:
                continue
            mail.status = SENDING
            mail.attempts += 1
            to, subject, body, attempts = mail.to, mail.subject, mail.body, mail.attempts
        try:
            send(to, subject, body)
            error = None
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:300]
        with sf() as s, s.begin():
            mail = s.get(m.OutboxEmail, mail_id)
            if error is None:
                mail.status, mail.sent_at, mail.last_error = SENT, now, None
                stats["sent"] += 1
            elif attempts >= max_attempts:
                mail.status, mail.last_error = FAILED, error
                stats["failed"] += 1
            else:
                mail.status, mail.next_attempt_at, mail.last_error = PENDING, now + backoff, error
                stats["retry"] += 1
    return stats
