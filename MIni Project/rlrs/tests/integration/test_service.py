"""Integration tests: service layer + real SQLite. Maps to Jira RLRS-3,6,8,9,10,11,12,13,14."""
import threading
from datetime import datetime, timedelta
import pytest
from rlrs_app import service
from rlrs_app.mailer import FileTransport
from rlrs_app.service import ApiError
from .conftest import NOW

D = "2026-11-09"  # Monday inside the 14-day window


def book(conn, user, eq, sh, eh, day=D, now=NOW, sm=0, em=0):
    return service.create_reservation(conn, user, eq, f"{day}T{sh:02d}:{sm:02d}", f"{day}T{eh:02d}:{em:02d}", now)


def err(fn, *a, **k):
    with pytest.raises(ApiError) as ex:
        fn(*a, **k)
    return ex.value


def count(conn, sql, *a):
    return conn.execute(sql, a).fetchone()[0]


# ---- RLRS-6: booking ----
def test_booking_creates_reservation_email_reminder_audit(conn, s1):
    r = book(conn, s1, 1, 10, 11)
    assert r["status"] == "Confirmed" and r["equipment"] == "Digital Oscilloscope"
    assert count(conn, "SELECT COUNT(*) FROM email_jobs WHERE to_email=? AND subject='Reservation confirmed'", s1["email"]) == 1
    assert count(conn, "SELECT COUNT(*) FROM reminder_jobs WHERE reservation_id=?", r["id"]) == 1
    assert count(conn, "SELECT COUNT(*) FROM audit WHERE action='reservation.create'") == 1


def test_conflict_returns_409_with_range_and_rolls_back(conn, s1, s2):
    book(conn, s1, 1, 10, 11)
    e = err(book, conn, s2, 1, 10, 11, sm=30)
    assert e.status == 409 and e.code == "CONFLICT" and e.details[0]["start"].startswith(f"{D}T10:00")
    assert count(conn, "SELECT COUNT(*) FROM reservations") == 1
    book(conn, s2, 1, 11, 12)  # back-to-back accepted


def test_rule_violations_return_400_with_codes(conn, s1):
    e = err(book, conn, s1, 1, 8, 9, day="2026-11-05")  # past + outside hours
    assert e.status == 400 and {"PAST_START", "OUTSIDE_HOURS"} <= {d["code"] for d in e.details}
    assert count(conn, "SELECT COUNT(*) FROM reservations") == 0


def test_inactive_equipment_cannot_be_booked(conn, s1, staff):
    service.update_equipment(conn, staff, 1, {"active": False}, NOW)
    assert err(book, conn, s1, 1, 10, 11).code == "EQUIPMENT_INACTIVE"


def test_concurrent_requests_for_same_slot_yield_exactly_one_booking(conn, tmp_path):
    from rlrs_app import db
    path = str(tmp_path / "t.db")
    for i in range(10):
        service.register_user(conn, f"U{i}", f"u{i}@lab.test", "secret1")
    users = [dict(r) for r in conn.execute("SELECT * FROM users WHERE email LIKE 'u%@lab.test'")]
    results, barrier = [], threading.Barrier(10)

    def go(u):
        c = db.connect(path)
        barrier.wait()
        try:
            book(c, u, 1, 14, 15)
            results.append("ok")
        except ApiError as e:
            results.append(e.code)
        finally:
            c.close()

    ts = [threading.Thread(target=go, args=(u,)) for u in users]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert results.count("ok") == 1 and results.count("CONFLICT") == 9
    assert count(conn, "SELECT COUNT(*) FROM reservations") == 1


# ---- RLRS-8: my reservations, cancel ----
def test_cancel_frees_slot_and_cancels_reminder(conn, s1, s2):
    r = book(conn, s1, 1, 10, 11)
    out = service.cancel_reservation(conn, s1, r["id"], NOW)
    assert out["status"] == "Cancelled"
    assert count(conn, "SELECT status FROM reminder_jobs WHERE reservation_id=?", r["id"]) == "Cancelled"
    book(conn, s2, 1, 10, 11)  # slot reusable
    assert [x["status"] for x in service.list_mine(conn, s1)] == ["Cancelled"]


def test_cancel_after_cutoff_refused(conn, s1):
    r = book(conn, s1, 1, 10, 11)
    late = datetime(2026, 11, 9, 9, 30)  # 30 min before start
    assert err(service.cancel_reservation, conn, s1, r["id"], late).code == "CUTOFF_PASSED"
    assert service.list_mine(conn, s1)[0]["status"] == "Confirmed"


def test_student_cannot_cancel_someone_elses_reservation(conn, s1, s2):
    r = book(conn, s1, 1, 10, 11)
    assert err(service.cancel_reservation, conn, s2, r["id"], NOW).status == 403
    assert service.list_mine(conn, s1)[0]["status"] == "Confirmed"


def test_rlrs8_remote_info_restricted_to_confirmed_holder_and_staff(conn, s1, s2, staff):
    service.update_equipment(conn, staff, 1, {"remote_info": "ssh://lab1-scope.local"}, NOW)
    service.update_equipment(conn, staff, 3, {"remote_info": "http://printer.local:8080"}, NOW)
    # Before booking, students do not see remote_info; staff does
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, s1)}[1] == ""
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, staff)}[1] == "ssh://lab1-scope.local"
    # Pending reservation does not expose remote_info
    pending = book(conn, s1, 3, 10, 11)
    assert pending["status"] == "Pending" and pending["remote_info"] == ""
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, s1)}[3] == ""
    # Confirmed reservation exposes remote_info only to its holder (s1), not to s2
    confirmed = book(conn, s1, 1, 12, 13)
    assert confirmed["status"] == "Confirmed" and confirmed["remote_info"] == "ssh://lab1-scope.local"
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, s1)}[1] == "ssh://lab1-scope.local"
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, s2)}[1] == ""
    # Cancelling revokes remote_info visibility
    service.cancel_reservation(conn, s1, confirmed["id"], NOW)
    assert {e["id"]: e["remote_info"] for e in service.list_equipment(conn, s1)}[1] == ""


# ---- RLRS-11: approval ----
def test_approval_flow_and_rejection(conn, s1, s2, staff):
    r = book(conn, s1, 3, 10, 11)  # 3D printer requires approval
    assert r["status"] == "Pending"
    assert count(conn, "SELECT COUNT(*) FROM reminder_jobs") == 0
    assert err(book, conn, s2, 3, 10, 11).code == "CONFLICT"  # pending still holds the slot
    assert service.approve_reservation(conn, staff, r["id"], NOW)["status"] == "Confirmed"
    assert count(conn, "SELECT COUNT(*) FROM reminder_jobs WHERE reservation_id=?", r["id"]) == 1
    r2 = book(conn, s2, 3, 12, 13)
    assert err(service.reject_reservation, conn, staff, r2["id"], "  ", NOW).code == "REASON_REQUIRED"
    assert service.reject_reservation(conn, staff, r2["id"], "Printer reserved for class", NOW)["status"] == "Rejected"
    book(conn, s1, 3, 12, 13)  # slot freed
    assert count(conn, "SELECT COUNT(*) FROM email_jobs WHERE subject='Reservation rejected'") == 1


def test_student_cannot_approve(conn, s1, s2):
    r = book(conn, s1, 3, 10, 11)
    assert err(service.approve_reservation, conn, s2, r["id"], NOW).status == 403


# ---- RLRS-12: maintenance ----
def test_maintenance_cancels_overlapping_and_blocks_new_bookings(conn, s1, s2, staff):
    a, b = book(conn, s1, 1, 10, 11), book(conn, s2, 1, 14, 15)
    out = service.add_maintenance(conn, staff, 1, f"{D}T09:00", f"{D}T12:00", "calibration", NOW)
    assert out["cancelled_reservation_ids"] == [a["id"]]
    assert service.list_mine(conn, s1)[0]["status"] == "Cancelled" and service.list_mine(conn, s2)[0]["status"] == "Confirmed"
    assert count(conn, "SELECT status FROM reminder_jobs WHERE reservation_id=?", a["id"]) == "Cancelled"
    assert count(conn, "SELECT COUNT(*) FROM email_jobs WHERE subject LIKE '%maintenance%'") == 1
    assert err(book, conn, s2, 1, 10, 11).code == "CONFLICT"
    states = {s["start"][11:16]: s["state"] for s in service.availability(conn, s1, 1, D, D, NOW)["slots"]}
    assert states["10:00"] == "maintenance" and states["12:00"] == "free" and states["14:00"] == "booked"


# ---- RLRS-13: attendance / audit ----
def test_attendance_only_after_slot_end_and_audited(conn, s1, staff):
    r = book(conn, s1, 1, 10, 11)
    assert err(service.mark_reservation_attendance, conn, staff, r["id"], "Completed", datetime(2026, 11, 9, 10, 30)).code == "ATTENDANCE_REJECTED"
    out = service.mark_reservation_attendance(conn, staff, r["id"], "NoShow", datetime(2026, 11, 9, 11, 5))
    assert out["status"] == "NoShow"
    assert any(e["action"] == "reservation.attendance" for e in service.audit_list(conn, staff))
    assert err(service.mark_reservation_attendance, conn, s1, r["id"], "Completed", datetime(2026, 11, 9, 12)).status == 403


def test_audit_never_contains_password(conn, s1, staff):
    service.login(conn, "student1@lab.test", "student123", NOW)
    blob = str(service.audit_list(conn, staff))
    assert "student123" not in blob and "pw_hash" not in blob
    assert err(service.audit_list, conn, s1).status == 403


# ---- RLRS-14: report ----
def test_utilisation_report_reconciles(conn, s1, s2, staff):
    a, b = book(conn, s1, 1, 10, 12), book(conn, s2, 1, 13, 14)
    c = book(conn, s1, 2, 9, 10)
    service.cancel_reservation(conn, s1, c["id"], NOW)
    service.mark_reservation_attendance(conn, staff, b["id"], "NoShow", datetime(2026, 11, 9, 15))
    rep = {r["equipment"]: r for r in service.utilisation(conn, staff, D, D, NOW)}
    o = rep["Digital Oscilloscope"]
    assert (o["booked_hours"], o["available_hours"], o["bookings"], o["no_shows"], o["utilisation_pct"]) == (3.0, 9.0, 2, 1, 33.33)
    assert rep["Logic Analyzer"]["cancellations"] == 1 and rep["Logic Analyzer"]["booked_hours"] == 0
    assert err(service.utilisation, conn, s1, D, D, NOW).status == 403


# ---- RLRS-9 / 10: emails and reminders against the database ----
def test_emails_flushed_once_and_retried_on_failure(conn, s1, transport):
    book(conn, s1, 1, 10, 11)

    class Down:
        def send(self, *a): raise ConnectionError("smtp down")

    assert service.flush_emails(conn, Down(), NOW)["retry"] == 1
    assert service.flush_emails(conn, transport, NOW + timedelta(minutes=1))["sent"] == 0  # backoff not elapsed
    assert service.flush_emails(conn, transport, NOW + timedelta(minutes=6))["sent"] == 1
    assert service.flush_emails(conn, transport, NOW + timedelta(minutes=12))["sent"] == 0  # exactly once
    assert len(transport.sent) == 1 and transport.sent[0][1] == "Reservation confirmed"


def test_reminder_sent_two_hours_before_exactly_once_and_survives_restart(conn, s1, transport):
    r = book(conn, s1, 1, 10, 11)
    assert service.run_reminders(conn, transport, datetime(2026, 11, 9, 7, 59))["sent"] == 0
    assert service.run_reminders(conn, transport, datetime(2026, 11, 9, 8, 0))["sent"] == 1
    assert service.run_reminders(conn, transport, datetime(2026, 11, 9, 8, 5))["sent"] == 0  # "restart": state lives in the DB
    assert [m[1] for m in transport.sent] == ["Reminder: upcoming lab reservation"]


def test_no_reminder_after_cancellation(conn, s1, transport):
    r = book(conn, s1, 1, 10, 11)
    service.cancel_reservation(conn, s1, r["id"], NOW)
    assert service.run_reminders(conn, transport, datetime(2026, 11, 9, 8, 30))["sent"] == 0 and transport.sent == []


# ---- RLRS-2 / 3: auth, equipment ----
def test_register_login_and_bad_credentials(conn):
    service.register_user(conn, "New", "new@lab.test", "secret1")
    token, u = service.login(conn, "NEW@lab.test", "secret1", NOW)
    assert u["role"] == "Student" and service.user_from_token(conn, token, NOW)["email"] == "new@lab.test"
    assert service.user_from_token(conn, token, NOW + timedelta(hours=9)) is None  # expired
    assert err(service.login, conn, "new@lab.test", "wrong", NOW).code == "BAD_CREDENTIALS"
    assert err(service.login, conn, "nobody@lab.test", "x", NOW).code == "BAD_CREDENTIALS"
    assert err(service.register_user, conn, "Dup", "new@lab.test", "secret1").status == 409
    assert err(service.register_user, conn, "X", "not-an-email", "secret1").status == 400
    assert "secret1" not in conn.execute("SELECT pw_hash FROM users WHERE email='new@lab.test'").fetchone()[0]


def test_equipment_management_permissions_and_search(conn, s1, staff):
    assert err(service.create_equipment, conn, s1, {"lab_id": 1, "name": "X"}, NOW).status == 403
    e = service.create_equipment(conn, staff, {"lab_id": 1, "name": "Spectrum Analyzer", "type": "Instrument", "requires_approval": True}, NOW)
    assert e["requires_approval"] is True
    assert [x["name"] for x in service.list_equipment(conn, s1, q="Spectrum")] == ["Spectrum Analyzer"]
    assert err(service.create_equipment, conn, staff, {"lab_id": 1, "name": "  "}, NOW).code == "BAD_INPUT"
    service.update_equipment(conn, staff, e["id"], {"active": False}, NOW)
    assert service.list_equipment(conn, s1, q="Spectrum") == []  # students no longer see inactive
    assert len(service.list_equipment(conn, staff, q="Spectrum")) == 1


def test_lab_hours_change_drives_the_calendar_grid(conn, s1, staff):
    service.update_lab(conn, staff, 1, {"open_time": "10:00", "close_time": "12:00", "slot_minutes": 60}, NOW)
    slots = service.availability(conn, s1, 1, D, D, NOW)["slots"]
    assert [s["start"][11:16] for s in slots] == ["10:00", "11:00"]
    assert err(service.update_lab, conn, staff, 1, {"open_time": "13:00", "close_time": "12:00"}, NOW).code == "BAD_INPUT"


def test_availability_marks_own_booked_and_validates_range(conn, s1, s2):
    book(conn, s1, 1, 10, 10, em=30)
    st = {s["start"][11:16]: (s["state"], s["label"]) for s in service.availability(conn, s1, 1, D, D, NOW)["slots"]}
    assert st["10:00"] == ("own", "Yours") and st["10:30"][0] == "free"
    assert {s["start"][11:16]: s["state"] for s in service.availability(conn, s2, 1, D, D, NOW)["slots"]}["10:00"] == "booked"
    assert err(service.availability, conn, s1, 1, D, "2026-12-30", NOW).code == "BAD_RANGE"
    assert err(service.availability, conn, s1, 1, "garbage", D, NOW).code == "BAD_DATE"


# ---- RLRS-6: timestamps stored in UTC ----
def test_rlrs6_timestamps_stored_in_utc(conn, s1):
    r = book(conn, s1, 1, 10, 11)  # input is lab-local time
    row = conn.execute("SELECT start_ts, end_ts, created_at FROM reservations WHERE id=?", (r["id"],)).fetchone()
    # default lab offset is +05:30 (IST): stored values must be UTC
    assert row["start_ts"] == f"{D}T04:30:00" and row["end_ts"] == f"{D}T05:30:00"
    assert row["created_at"] == "2026-11-06T02:30:00"  # NOW = Fri 08:00 IST -> 02:30 UTC
    # API responses still speak lab-local time
    assert r["start"] == f"{D}T10:00:00" and r["end"] == f"{D}T11:00:00"
    slots = {s["start"][11:16]: s["state"] for s in service.availability(conn, s1, 1, D, D, NOW)["slots"]}
    assert slots["10:00"] == "own"  # converted back to lab-local for display


# ---- RLRS-11: only that lab's in-charge can act ----
def test_rlrs11_other_lab_incharge_denied(conn, s1, staff):
    # Equipment 3 (3D Printer) needs approval and sits in lab 2; give lab 2 its own in-charge
    # so `staff` (in-charge of lab 1) is no longer that lab's manager.
    other = service.register_user(conn, "Other In-charge", "incharge2@lab.test", "incharge123", "LabInCharge")
    conn.execute("UPDATE labs SET incharge_id=? WHERE id=2", (other["id"],))
    r = book(conn, s1, 3, 10, 11)
    assert r["status"] == "Pending"
    # an in-charge from another lab gets 403 on approve and reject
    assert err(service.approve_reservation, conn, staff, r["id"], NOW).status == 403
    assert err(service.reject_reservation, conn, staff, r["id"], "not my lab", NOW).status == 403
    # lab 2's own in-charge can act
    other_user = dict(conn.execute("SELECT * FROM users WHERE email='incharge2@lab.test'").fetchone())
    assert service.approve_reservation(conn, other_user, r["id"], NOW)["status"] == "Confirmed"
