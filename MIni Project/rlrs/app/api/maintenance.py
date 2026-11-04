"""RLRS-12: maintenance block endpoints, plus the equipment schedule feed the calendar
(RLRS-7) reads to show booked and maintenance slots."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import get_now, get_session, staff_only
from app.db import to_utc_naive
from app.engine import maintenance
from app.engine.reminders import ACTIVE_VALUES

router = APIRouter(tags=["maintenance"])


class BlockIn(BaseModel):
    equipment_id: int
    start: datetime = Field(description="ISO 8601; timezone offset recommended, naive = UTC")
    end: datetime
    reason: str = Field(default="", max_length=300)


class BlockOut(BaseModel):
    id: int
    equipment_id: int
    start_utc: datetime
    end_utc: datetime
    reason: str

    model_config = {"from_attributes": True}


class BlockCreated(BaseModel):
    block: BlockOut
    cancelled_reservation_ids: list[int]


class ScheduleItem(BaseModel):
    kind: str  # "reservation" | "maintenance"
    id: int
    start_utc: datetime
    end_utc: datetime
    status: str | None = None
    reason: str | None = None


@router.post("/api/maintenance-blocks", response_model=BlockCreated, status_code=201)
def create_block(body: BlockIn, session: Session = Depends(get_session),
                 now: datetime = Depends(get_now), user: m.User = Depends(staff_only)):
    try:
        result = maintenance.create_block(session, body.equipment_id, to_utc_naive(body.start),
                                          to_utc_naive(body.end), body.reason, user, now)
    except maintenance.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except maintenance.InvalidBlock as e:
        raise HTTPException(422, str(e))
    session.commit()
    return BlockCreated(block=BlockOut.model_validate(result.block),
                        cancelled_reservation_ids=[r.id for r in result.cancelled])


@router.get("/api/maintenance-blocks", response_model=list[BlockOut])
def list_blocks(equipment_id: int | None = None, session: Session = Depends(get_session)):
    q = select(m.MaintenanceBlock).order_by(m.MaintenanceBlock.start_utc)
    if equipment_id is not None:
        q = q.where(m.MaintenanceBlock.equipment_id == equipment_id)
    return list(session.scalars(q))


@router.get("/api/equipment/{equipment_id}/schedule", response_model=list[ScheduleItem])
def equipment_schedule(equipment_id: int, start: datetime = Query(alias="from"),
                       end: datetime = Query(alias="to"), session: Session = Depends(get_session)):
    """Busy slots for one piece of equipment in [from, to). No personal data: the calendar
    only needs to know a slot is taken or under maintenance."""
    if session.get(m.Equipment, equipment_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Equipment {equipment_id} not found.")
    s, e = to_utc_naive(start), to_utc_naive(end)
    if e <= s:
        raise HTTPException(422, "'to' must be after 'from'.")
    res = session.scalars(select(m.Reservation).where(
        m.Reservation.equipment_id == equipment_id, m.Reservation.status.in_(ACTIVE_VALUES),
        m.Reservation.start_utc < e, m.Reservation.end_utc > s))
    blocks = session.scalars(select(m.MaintenanceBlock).where(
        m.MaintenanceBlock.equipment_id == equipment_id,
        m.MaintenanceBlock.start_utc < e, m.MaintenanceBlock.end_utc > s))
    items = [ScheduleItem(kind="reservation", id=r.id, start_utc=r.start_utc, end_utc=r.end_utc, status=r.status)
             for r in res]
    items += [ScheduleItem(kind="maintenance", id=b.id, start_utc=b.start_utc, end_utc=b.end_utc, reason=b.reason)
              for b in blocks]
    return sorted(items, key=lambda i: i.start_utc)
