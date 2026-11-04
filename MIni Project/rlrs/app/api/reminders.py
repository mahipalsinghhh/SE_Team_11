"""RLRS-10: staff view of reminder jobs (so stuck/failed reminders are visible)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import get_session, staff_only

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderOut(BaseModel):
    id: int
    reservation_id: int
    send_at: datetime
    status: str
    attempts: int
    sent_at: datetime | None
    last_error: str | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ReminderOut])
def list_reminders(status: str | None = Query(default=None), limit: int = Query(default=100, le=500),
                   session: Session = Depends(get_session), _=Depends(staff_only)):
    q = select(m.ReminderJob).order_by(m.ReminderJob.send_at.desc()).limit(limit)
    if status:
        q = q.where(m.ReminderJob.status == status)
    return list(session.scalars(q))
