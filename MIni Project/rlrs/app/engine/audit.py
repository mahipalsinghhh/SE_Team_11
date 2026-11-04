"""RLRS-13: persistent audit trail (RLRS-F-021, SR-007).

Call record_audit() inside the same transaction as the change it describes, so an audit row
exists if and only if the change was committed. Details pass through rlrs_core.audit.redact,
so passwords, tokens and other secrets are never stored.

Who calls it: attendance and maintenance (here); reservation create/cancel (RLRS-6/8) and
approvals (RLRS-11) should call it too.
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from sqlalchemy.orm import Session

from rlrs_core.audit import redact

from app import models as m


def _jsonable(v: Any) -> Any:
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in v]
    return v


def record_audit(session: Session, actor: m.User | None, action: str, entity: str,
                 entity_id: int | None, at: datetime, **details: Any) -> m.AuditEvent:
    ev = m.AuditEvent(
        actor_id=actor.id if actor else None,
        actor=f"{actor.email} ({actor.role})" if actor else "system",
        action=action, entity=entity, entity_id=entity_id, at=at,
        details=_jsonable(redact(details)),
    )
    session.add(ev)
    return ev
