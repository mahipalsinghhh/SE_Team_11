"""RLRS-14: utilisation and no-show report endpoint."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session, staff_only
from app.db import to_utc_naive
from app.engine.report import build_report

router = APIRouter(prefix="/api/reports", tags=["reports"])

MAX_RANGE = timedelta(days=366)


class ReportRowOut(BaseModel):
    lab_id: int
    lab: str
    equipment_id: int
    equipment: str
    booked_hours: float
    available_hours: float
    utilisation_pct: float
    bookings: int
    cancellations: int
    no_shows: int

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    from_utc: datetime
    to_utc: datetime
    rows: list[ReportRowOut]


@router.get("/utilisation", response_model=ReportOut)
def utilisation(start: datetime = Query(alias="from", description="ISO 8601, offset recommended"),
                end: datetime = Query(alias="to"), lab_id: int | None = None,
                session: Session = Depends(get_session), _=Depends(staff_only)):
    s, e = to_utc_naive(start), to_utc_naive(end)
    if e <= s:
        raise HTTPException(422, "'to' must be after 'from'.")
    if e - s > MAX_RANGE:
        raise HTTPException(422, "Date range can be at most one year.")
    return ReportOut(from_utc=s, to_utc=e, rows=build_report(session, s, e, lab_id))
