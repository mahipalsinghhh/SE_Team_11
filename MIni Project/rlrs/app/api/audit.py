"""RLRS-13: audit log view for lab in-charges and admins."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import get_session, staff_only

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditOut(BaseModel):
    id: int
    actor: str
    action: str
    entity: str
    entity_id: int | None
    at: datetime
    details: dict

    model_config = {"from_attributes": True}


@router.get("", response_model=list[AuditOut])
def list_audit(entity: str | None = None, entity_id: int | None = None,
               limit: int = Query(default=100, le=500),
               session: Session = Depends(get_session), _=Depends(staff_only)):
    q = select(m.AuditEvent).order_by(m.AuditEvent.at.desc(), m.AuditEvent.id.desc()).limit(limit)
    if entity:
        q = q.where(m.AuditEvent.entity == entity)
    if entity_id is not None:
        q = q.where(m.AuditEvent.entity_id == entity_id)
    return list(session.scalars(q))
