"""RLRS-13: attendance marking endpoint."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rlrs_core.types import Status

from app import models as m
from app.api.deps import get_now, get_session, staff_only
from app.engine import attendance

router = APIRouter(prefix="/api/reservations", tags=["attendance"])


class AttendanceIn(BaseModel):
    outcome: Literal["Completed", "NoShow"]


class ReservationOut(BaseModel):
    id: int
    user_id: int
    equipment_id: int
    start_utc: datetime
    end_utc: datetime
    status: str

    model_config = {"from_attributes": True}


@router.post("/{reservation_id}/attendance", response_model=ReservationOut)
def mark_attendance(reservation_id: int, body: AttendanceIn,
                    session: Session = Depends(get_session), now: datetime = Depends(get_now),
                    user: m.User = Depends(staff_only)):
    try:
        res = attendance.mark(session, reservation_id, Status(body.outcome), user, now)
    except attendance.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except attendance.AttendanceError as e:
        # slot not ended yet, or reservation not Confirmed: a state conflict
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    session.commit()
    return res
