"""RLRS-13 | TC-ATT-01, TC-AUDIT-01"""
import pytest
from datetime import timedelta
from rlrs_core.attendance import AttendanceError, mark_attendance
from rlrs_core.audit import AuditLog
from rlrs_core.types import Status
from .helpers import NOW, iv, res


def test_mark_completed_and_no_show_after_end():
    r = res(1, 1, 7, iv(0, 9, 0, 10, 0))
    mark_attendance(r, Status.COMPLETED, r.interval.end)
    assert r.status == Status.COMPLETED
    r2 = res(2, 1, 7, iv(0, 9, 0, 10, 0))
    mark_attendance(r2, Status.NO_SHOW, r2.interval.end + timedelta(hours=1))
    assert r2.status == Status.NO_SHOW


def test_cannot_mark_before_slot_ends():
    r = res(1, 1, 7, iv(0, 9, 0, 10, 0))
    with pytest.raises(AttendanceError):
        mark_attendance(r, Status.COMPLETED, r.interval.end - timedelta(minutes=1))
    assert r.status == Status.CONFIRMED


def test_only_confirmed_and_valid_outcomes():
    r = res(1, 1, 7, iv(0, 9, 0, 10, 0), Status.CANCELLED)
    with pytest.raises(AttendanceError):
        mark_attendance(r, Status.COMPLETED, r.interval.end)
    r2 = res(2, 1, 7, iv(0, 9, 0, 10, 0))
    with pytest.raises(AttendanceError):
        mark_attendance(r2, Status.CANCELLED, r2.interval.end)


def test_audit_records_actor_action_time_and_redacts_secrets():
    log = AuditLog()
    ev = log.record("lab.incharge", "reservation.approve", NOW, reservation_id=5,
                    password="hunter2", smtp_token="abc", note="ok")
    assert ev.actor == "lab.incharge" and ev.action == "reservation.approve" and ev.at == NOW
    assert ev.details["reservation_id"] == 5 and ev.details["note"] == "ok"
    assert ev.details["password"] == "[REDACTED]" and ev.details["smtp_token"] == "[REDACTED]"
    assert len(log.events()) == 1
