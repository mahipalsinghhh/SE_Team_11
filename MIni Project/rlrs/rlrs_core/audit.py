"""RLRS-13 (part): audit trail that never stores secrets (RLRS-F-021, SR-007)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

SENSITIVE_KEYS = ("password", "passwd", "secret", "token", "api_key", "authorization")


def redact(details: dict[str, Any]) -> dict[str, Any]:
    return {k: ("[REDACTED]" if any(s in k.lower() for s in SENSITIVE_KEYS) else v)
            for k, v in details.items()}


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    at: datetime
    details: dict = field(default_factory=dict)


class AuditLog:
    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, actor: str, action: str, at: datetime, **details) -> AuditEvent:
        ev = AuditEvent(actor, action, at, redact(details))
        self._events.append(ev)
        return ev

    def events(self) -> list[AuditEvent]:
        return list(self._events)
