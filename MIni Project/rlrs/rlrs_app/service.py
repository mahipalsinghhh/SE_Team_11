"""RLRS service layer: SQLite persistence around the pure rlrs_core logic.

Every public function takes an open connection and an explicit `now` so tests can use a fake clock.
Lab times are stored as lab-local naive ISO strings (no time-zone conversion in this build).
"""
from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta

from rlrs_core import reminders as rem
from rlrs_core.attendance import AttendanceError, mark_attendance
from rlrs_core.audit import redact
from rlrs_core.conflict import find_conflicts
from rlrs_core.maintenance import apply_block
from rlrs_core.report import utilisation_report
from rlrs_core.rules import LabConfig, validate_booking
from rlrs_core.types import Interval, MaintenanceBlock, Reservation, Status

from . import security

STAFF = ("LabInCharge", "Admin")
ROLES = ("Student", "LabInCharge", "Admin")
CANCEL_CUTOFF = timedelta(minutes=60)
SESSION_TTL = timedelta(hours=8)
FMT_S = "%Y-%m-%dT%H:%M:%S"
FMT_M = "%Y-%m-%dT%H:%M"
ACTIVE_SQL = "('Pending','Confirmed')"


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


# ---------- helpers ----------
def parse_dt(s) -> datetime:
    for fmt in (FMT_S, FMT_M):
        try:
            return datetime.strptime(s, fmt)
        except (TypeError, ValueError):
            pass
    raise ApiError(400, "BAD_TIME", "Times must look like 2026-11-09T10:00.")


def parse_date(s) -> date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ApiError(400, "BAD_DATE", "Dates must look like 2026-11-09.")


def fmt(dt: datetime) -> str:
    return dt.strftime(FMT_S)


@contextmanager
def tx(conn: sqlite3.Connection):
    """One write transaction. BEGIN IMMEDIATE takes the database write lock up front, so
    'check for conflicts then insert' cannot interleave with another request."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def require_role(user, *roles):
    if user["role"] not in roles:
        raise ApiError(403, "FORBIDDEN", "You do not have permission to do that.")


def _cfg(lab) -> LabConfig:
    return LabConfig(time.fromisoformat(lab["open_time"]), time.fromisoformat(lab["close_time"]),
                     lab["slot_minutes"], lab["max_duration"], lab["advance_days"], lab["max_active"])


def _res(r) -> Reservation:
    return Reservation(r["id"], r["user_id"], r["equipment_id"],
                       Interval(parse_dt(r["start_ts"]), parse_dt(r["end_ts"])), Status(r["status"]))


def _block(r) -> MaintenanceBlock:
    return MaintenanceBlock(r["id"], r["equipment_id"], Interval(parse_dt(r["start_ts"]), parse_dt(r["end_ts"])), r["reason"])


def _audit(conn, actor, action, now, **details):
    conn.execute("INSERT INTO audit(actor,action,at,details) VALUES(?,?,?,?)",
                 (actor, action, fmt(now), json.dumps(redact(details), default=str)))


def _email(conn, to, subject, body, now):
    conn.execute("INSERT INTO email_jobs(to_email,subject,body,created_at) VALUES(?,?,?,?)", (to, subject, body, fmt(now)))


def _get(conn, table, id_, what):
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (id_,)).fetchone()
    if not row:
        raise ApiError(404, "NOT_FOUND", f"{what} not found.")
    return row


def _can_manage_lab(conn, user, lab_id) -> bool:
    if user["role"] == "Admin":
        return True
    lab = conn.execute("SELECT incharge_id FROM labs WHERE id=?", (lab_id,)).fetchone()
    return bool(lab) and user["role"] == "LabInCharge" and lab["incharge_id"] == user["id"]


def _require_lab_staff(conn, user, lab_id):
    if not _can_manage_lab(conn, user, lab_id):
        raise ApiError(403, "FORBIDDEN", "You do not manage this lab.")


def public_user(u):
    return {"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"]}


def _res_dict(conn, r):
    eq = conn.execute("SELECT e.name, l.name AS lab FROM equipment e JOIN labs l ON l.id=e.lab_id WHERE e.id=?",
                      (r["equipment_id"],)).fetchone()
    return {"id": r["id"], "equipment_id": r["equipment_id"], "equipment": eq["name"], "lab": eq["lab"],
            "start": r["start_ts"], "end": r["end_ts"], "status": r["status"], "reason": r["reason"]}


# ---------- users / auth ----------
def register_user(conn, name, email, password, role="Student", now=None):
    name, email = (name or "").strip(), (email or "").strip().lower()
    if not name or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ApiError(400, "BAD_INPUT", "A name and a valid email are required.")
    if len(password or "") < 6:
        raise ApiError(400, "BAD_INPUT", "Password must be at least 6 characters.")
    if role not in ROLES:
        raise ApiError(400, "BAD_INPUT", "Unknown role.")
    try:
        cur = conn.execute("INSERT INTO users(name,email,role,pw_hash) VALUES(?,?,?,?)",
                           (name, email, role, security.hash_password(password)))
    except sqlite3.IntegrityError:
        raise ApiError(409, "EMAIL_TAKEN", "That email is already registered.")
    return {"id": cur.lastrowid, "name": name, "email": email, "role": role}


def login(conn, email, password, now):
    row = conn.execute("SELECT * FROM users WHERE email=?", ((email or "").strip().lower(),)).fetchone()
    ok = security.verify_password(password or "", row["pw_hash"] if row else security.DUMMY_HASH)
    if not row or not ok:
        raise ApiError(401, "BAD_CREDENTIALS", "Invalid email or password.")
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)", (token, row["id"], fmt(now + SESSION_TTL)))
    _audit(conn, row["email"], "auth.login", now)
    return token, public_user(row)


def logout(conn, token):
    conn.execute("DELETE FROM sessions WHERE token=?", (token,))


def user_from_token(conn, token, now):
    if not token:
        return None
    conn.execute("DELETE FROM sessions WHERE expires < ?", (fmt(now),))
    row = conn.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?", (token,)).fetchone()
    return dict(row) if row else None


# ---------- labs / equipment ----------
def list_labs(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM labs ORDER BY name")]


def update_lab(conn, user, lab_id, data, now):
    lab = _get(conn, "labs", lab_id, "Lab")
    _require_lab_staff(conn, user, lab_id)
    new = {k: data.get(k, lab[k]) for k in ("open_time", "close_time", "slot_minutes", "max_duration", "advance_days", "max_active")}
    try:
        o, c = time.fromisoformat(new["open_time"]), time.fromisoformat(new["close_time"])
        ints = [int(new[k]) for k in ("slot_minutes", "max_duration", "advance_days", "max_active")]
    except (ValueError, TypeError):
        raise ApiError(400, "BAD_INPUT", "Invalid lab settings.")
    if o >= c or not (5 <= ints[0] <= 240) or ints[1] < ints[0] or ints[2] < 1 or ints[3] < 1:
        raise ApiError(400, "BAD_INPUT", "Opening must be before closing; slot 5-240 min; duration >= slot.")
    with tx(conn):
        conn.execute("UPDATE labs SET open_time=?,close_time=?,slot_minutes=?,max_duration=?,advance_days=?,max_active=? WHERE id=?",
                     (new["open_time"], new["close_time"], *ints, lab_id))
        _audit(conn, user["email"], "lab.update", now, lab_id=lab_id)
    return dict(_get(conn, "labs", lab_id, "Lab"))


def _eq_dict(r):
    d = dict(r)
    d["requires_approval"], d["active"] = bool(d["requires_approval"]), bool(d["active"])
    return d


def list_equipment(conn, user, lab_id=None, type_=None, q=None):
    sql, args = "SELECT e.*, l.name AS lab FROM equipment e JOIN labs l ON l.id=e.lab_id WHERE 1=1", []
    if user["role"] == "Student":
        sql += " AND e.active=1"
    if lab_id:
        sql, args = sql + " AND e.lab_id=?", args + [lab_id]
    if type_:
        sql, args = sql + " AND e.type=?", args + [type_]
    if q:
        like = f"%{q}%"
        sql, args = sql + " AND (e.name LIKE ? OR e.description LIKE ?)", args + [like, like]
    return [_eq_dict(r) for r in conn.execute(sql + " ORDER BY l.name, e.name", args)]


def _eq_fields(data, existing=None):
    name = (data.get("name", existing["name"] if existing else "") or "").strip()
    if not name:
        raise ApiError(400, "BAD_INPUT", "Equipment name is required.")
    return (name, (data.get("type", existing["type"] if existing else "") or "").strip(),
            (data.get("description", existing["description"] if existing else "") or "").strip(),
            1 if data.get("requires_approval", bool(existing["requires_approval"]) if existing else False) else 0,
            (data.get("remote_info", existing["remote_info"] if existing else "") or "").strip())


def create_equipment(conn, user, data, now):
    lab_id = data.get("lab_id")
    _get(conn, "labs", lab_id, "Lab")
    _require_lab_staff(conn, user, lab_id)
    name, type_, desc, req, remote = _eq_fields(data)
    with tx(conn):
        cur = conn.execute("INSERT INTO equipment(lab_id,name,type,description,requires_approval,remote_info) VALUES(?,?,?,?,?,?)",
                           (lab_id, name, type_, desc, req, remote))
        _audit(conn, user["email"], "equipment.create", now, equipment_id=cur.lastrowid)
    return _eq_dict(_get(conn, "equipment", cur.lastrowid, "Equipment"))


def update_equipment(conn, user, eq_id, data, now):
    eq = _get(conn, "equipment", eq_id, "Equipment")
    _require_lab_staff(conn, user, eq["lab_id"])
    name, type_, desc, req, remote = _eq_fields(data, eq)
    active = 1 if data.get("active", bool(eq["active"])) else 0
    with tx(conn):
        conn.execute("UPDATE equipment SET name=?,type=?,description=?,requires_approval=?,remote_info=?,active=? WHERE id=?",
                     (name, type_, desc, req, remote, active, eq_id))
        _audit(conn, user["email"], "equipment.update", now, equipment_id=eq_id, active=bool(active))
    return _eq_dict(_get(conn, "equipment", eq_id, "Equipment"))


# ---------- availability ----------
def availability(conn, user, eq_id, d_from, d_to, now):
    df, dt = parse_date(d_from), parse_date(d_to)
    if dt < df or (dt - df).days > 30:
        raise ApiError(400, "BAD_RANGE", "Date range must be 1 to 31 days.")
    eq = _get(conn, "equipment", eq_id, "Equipment")
    cfg = _cfg(_get(conn, "labs", eq["lab_id"], "Lab"))
    w0, w1 = fmt(datetime.combine(df, time.min)), fmt(datetime.combine(dt + timedelta(days=1), time.min))
    ress = [r for r in conn.execute(f"SELECT * FROM reservations WHERE equipment_id=? AND status IN {ACTIVE_SQL} AND start_ts<? AND end_ts>?", (eq_id, w1, w0))]
    blocks = [_block(r) for r in conn.execute("SELECT * FROM maintenance WHERE equipment_id=? AND start_ts<? AND end_ts>?", (eq_id, w1, w0))]
    step, slots, d = timedelta(minutes=cfg.slot_minutes), [], df
    while d <= dt:
        cur, close = datetime.combine(d, cfg.open_time), datetime.combine(d, cfg.close_time)
        while cur + step <= close:
            iv = Interval(cur, cur + step)
            state, rid, label = "free", None, "Free"
            if any(b.interval.overlaps(iv) for b in blocks):
                state, label = "maintenance", "Maintenance"
            else:
                for r in ress:
                    if parse_dt(r["start_ts"]) < iv.end and iv.start < parse_dt(r["end_ts"]):
                        mine = r["user_id"] == user["id"]
                        state, rid = ("own" if mine else "booked"), (r["id"] if mine else None)
                        label = ("Yours" if mine else "Booked") + (" (pending)" if r["status"] == "Pending" else "")
                        break
            if state == "free" and cur < now:
                state, label = "past", "Past"
            slots.append({"start": fmt(cur), "end": fmt(cur + step), "state": state, "label": label, "reservation_id": rid})
            cur += step
        d += timedelta(days=1)
    return {"equipment_id": eq_id, "slot_minutes": cfg.slot_minutes, "slots": slots}


# ---------- reservations ----------
def _schedule_reminder(conn, res: Reservation, now):
    job = rem.plan_reminder(res, now)
    if job:
        conn.execute("INSERT OR REPLACE INTO reminder_jobs(reservation_id,send_at,status,attempts) VALUES(?,?, 'Pending',0)",
                     (res.id, fmt(job.send_at)))


def _cancel_reminders(conn, ids):
    for rid in ids:
        conn.execute("UPDATE reminder_jobs SET status='Cancelled' WHERE reservation_id=? AND status='Pending'", (rid,))


def create_reservation(conn, user, eq_id, start, end, now):
    s, e = parse_dt(start), parse_dt(end)
    if e <= s:
        raise ApiError(400, "BAD_RANGE", "End must be after start.")
    with tx(conn):
        eq = _get(conn, "equipment", eq_id, "Equipment")
        if not eq["active"]:
            raise ApiError(409, "EQUIPMENT_INACTIVE", "This equipment is not available for booking.")
        cfg = _cfg(_get(conn, "labs", eq["lab_id"], "Lab"))
        iv = Interval(s, e)
        mine = [_res(r) for r in conn.execute(f"SELECT * FROM reservations WHERE user_id=? AND status IN {ACTIVE_SQL}", (user["id"],))]
        violations = validate_booking(user["id"], eq_id, iv, now, cfg, mine)
        if violations:
            raise ApiError(400, "RULE_VIOLATION", "Booking rules violated.", [{"code": v.code, "message": v.message} for v in violations])
        others = [_res(r) for r in conn.execute(f"SELECT * FROM reservations WHERE equipment_id=? AND status IN {ACTIVE_SQL} AND start_ts<? AND end_ts>?", (eq_id, fmt(e), fmt(s)))]
        blocks = [_block(r) for r in conn.execute("SELECT * FROM maintenance WHERE equipment_id=? AND start_ts<? AND end_ts>?", (eq_id, fmt(e), fmt(s)))]
        conflicts = find_conflicts(eq_id, iv, others, blocks)
        if conflicts:
            raise ApiError(409, "CONFLICT", "That time slot is not available.",
                           [{"kind": c.kind, "start": fmt(c.interval.start), "end": fmt(c.interval.end)} for c in conflicts])
        status = Status.PENDING if eq["requires_approval"] else Status.CONFIRMED
        cur = conn.execute("INSERT INTO reservations(user_id,equipment_id,start_ts,end_ts,status,created_at) VALUES(?,?,?,?,?,?)",
                           (user["id"], eq_id, fmt(s), fmt(e), status.value, fmt(now)))
        res = Reservation(cur.lastrowid, user["id"], eq_id, iv, status)
        if status == Status.CONFIRMED:
            _schedule_reminder(conn, res, now)
            _email(conn, user["email"], "Reservation confirmed",
                   f"Your reservation for {eq['name']} on {s:%Y-%m-%d} {s:%H:%M}-{e:%H:%M} is confirmed.", now)
        else:
            _email(conn, user["email"], "Reservation request received",
                   f"Your request for {eq['name']} on {s:%Y-%m-%d} {s:%H:%M}-{e:%H:%M} awaits approval.", now)
        _audit(conn, user["email"], "reservation.create", now, reservation_id=res.id, status=status.value)
    return _res_dict(conn, _get(conn, "reservations", res.id, "Reservation"))


def list_mine(conn, user):
    return [_res_dict(conn, r) for r in conn.execute("SELECT * FROM reservations WHERE user_id=? ORDER BY start_ts DESC", (user["id"],))]


def cancel_reservation(conn, user, res_id, now):
    with tx(conn):
        r = _get(conn, "reservations", res_id, "Reservation")
        eq = _get(conn, "equipment", r["equipment_id"], "Equipment")
        owner = r["user_id"] == user["id"]
        if not owner and not _can_manage_lab(conn, user, eq["lab_id"]):
            raise ApiError(403, "FORBIDDEN", "You can only cancel your own reservations.")
        if r["status"] not in ("Pending", "Confirmed"):
            raise ApiError(409, "NOT_CANCELLABLE", f"A {r['status']} reservation cannot be cancelled.")
        if owner and user["role"] == "Student" and now > parse_dt(r["start_ts"]) - CANCEL_CUTOFF:
            raise ApiError(409, "CUTOFF_PASSED", "Reservations cannot be cancelled within 60 minutes of the start.")
        conn.execute("UPDATE reservations SET status='Cancelled' WHERE id=?", (res_id,))
        _cancel_reminders(conn, [res_id])
        holder = conn.execute("SELECT email FROM users WHERE id=?", (r["user_id"],)).fetchone()
        _email(conn, holder["email"], "Reservation cancelled", f"Your reservation for {eq['name']} at {r['start_ts'][:16]} was cancelled.", now)
        _audit(conn, user["email"], "reservation.cancel", now, reservation_id=res_id)
    return _res_dict(conn, _get(conn, "reservations", res_id, "Reservation"))


def _staff_labs(conn, user):
    if user["role"] == "Admin":
        return [r["id"] for r in conn.execute("SELECT id FROM labs")]
    return [r["id"] for r in conn.execute("SELECT id FROM labs WHERE incharge_id=?", (user["id"],))]


def manage_list(conn, user, status=None):
    require_role(user, *STAFF)
    labs = _staff_labs(conn, user)
    if not labs:
        return []
    marks = ",".join("?" * len(labs))
    sql = f"SELECT r.*, u.name AS who FROM reservations r JOIN equipment e ON e.id=r.equipment_id JOIN users u ON u.id=r.user_id WHERE e.lab_id IN ({marks})"
    args = list(labs)
    if status:
        sql, args = sql + " AND r.status=?", args + [status]
    out = []
    for r in conn.execute(sql + " ORDER BY r.start_ts DESC LIMIT 100", args):
        d = _res_dict(conn, r)
        d["user"] = r["who"]
        out.append(d)
    return out


def approve_reservation(conn, user, res_id, now):
    with tx(conn):
        r = _get(conn, "reservations", res_id, "Reservation")
        eq = _get(conn, "equipment", r["equipment_id"], "Equipment")
        _require_lab_staff(conn, user, eq["lab_id"])
        if r["status"] != "Pending":
            raise ApiError(409, "NOT_PENDING", "Only Pending reservations can be approved.")
        conn.execute("UPDATE reservations SET status='Confirmed' WHERE id=?", (res_id,))
        res = _res(_get(conn, "reservations", res_id, "Reservation"))
        _schedule_reminder(conn, res, now)
        holder = conn.execute("SELECT email FROM users WHERE id=?", (r["user_id"],)).fetchone()
        _email(conn, holder["email"], "Reservation approved", f"Your reservation for {eq['name']} at {r['start_ts'][:16]} was approved.", now)
        _audit(conn, user["email"], "reservation.approve", now, reservation_id=res_id)
    return _res_dict(conn, _get(conn, "reservations", res_id, "Reservation"))


def reject_reservation(conn, user, res_id, reason, now):
    reason = (reason or "").strip()
    if not reason:
        raise ApiError(400, "REASON_REQUIRED", "A reason is required to reject a reservation.")
    with tx(conn):
        r = _get(conn, "reservations", res_id, "Reservation")
        eq = _get(conn, "equipment", r["equipment_id"], "Equipment")
        _require_lab_staff(conn, user, eq["lab_id"])
        if r["status"] != "Pending":
            raise ApiError(409, "NOT_PENDING", "Only Pending reservations can be rejected.")
        conn.execute("UPDATE reservations SET status='Rejected', reason=? WHERE id=?", (reason, res_id))
        holder = conn.execute("SELECT email FROM users WHERE id=?", (r["user_id"],)).fetchone()
        _email(conn, holder["email"], "Reservation rejected", f"Your reservation for {eq['name']} at {r['start_ts'][:16]} was rejected: {reason}", now)
        _audit(conn, user["email"], "reservation.reject", now, reservation_id=res_id, reason=reason)
    return _res_dict(conn, _get(conn, "reservations", res_id, "Reservation"))


def add_maintenance(conn, user, eq_id, start, end, reason, now):
    s, e = parse_dt(start), parse_dt(end)
    if e <= s:
        raise ApiError(400, "BAD_RANGE", "End must be after start.")
    with tx(conn):
        eq = _get(conn, "equipment", eq_id, "Equipment")
        _require_lab_staff(conn, user, eq["lab_id"])
        cur = conn.execute("INSERT INTO maintenance(equipment_id,start_ts,end_ts,reason) VALUES(?,?,?,?)", (eq_id, fmt(s), fmt(e), (reason or "").strip()))
        block = MaintenanceBlock(cur.lastrowid, eq_id, Interval(s, e), reason or "")
        active = [_res(r) for r in conn.execute(f"SELECT * FROM reservations WHERE equipment_id=? AND status IN {ACTIVE_SQL}", (eq_id,))]
        hit = apply_block(block, active)  # core logic marks overlapping reservations Cancelled
        for r in hit:
            conn.execute("UPDATE reservations SET status='Cancelled', reason=? WHERE id=?", ("Maintenance: " + block.reason, r.id))
            holder = conn.execute("SELECT email FROM users WHERE id=?", (r.user_id,)).fetchone()
            _email(conn, holder["email"], "Reservation cancelled for maintenance",
                   f"Your reservation for {eq['name']} at {fmt(r.interval.start)[:16]} was cancelled: maintenance ({block.reason or 'scheduled'}).", now)
        _cancel_reminders(conn, [r.id for r in hit])
        _audit(conn, user["email"], "maintenance.create", now, block_id=block.id, equipment_id=eq_id, cancelled=[r.id for r in hit])
    return {"block_id": block.id, "cancelled_reservation_ids": [r.id for r in hit]}


def mark_reservation_attendance(conn, user, res_id, outcome, now):
    try:
        status = Status(outcome)
    except ValueError:
        raise ApiError(400, "BAD_INPUT", "Outcome must be Completed or NoShow.")
    with tx(conn):
        r = _get(conn, "reservations", res_id, "Reservation")
        eq = _get(conn, "equipment", r["equipment_id"], "Equipment")
        _require_lab_staff(conn, user, eq["lab_id"])
        res = _res(r)
        try:
            mark_attendance(res, status, now)
        except AttendanceError as ex:
            raise ApiError(409, "ATTENDANCE_REJECTED", str(ex))
        conn.execute("UPDATE reservations SET status=? WHERE id=?", (res.status.value, res_id))
        _audit(conn, user["email"], "reservation.attendance", now, reservation_id=res_id, outcome=res.status.value)
    return _res_dict(conn, _get(conn, "reservations", res_id, "Reservation"))


def utilisation(conn, user, d_from, d_to, now):
    require_role(user, *STAFF)
    df, dt = parse_date(d_from), parse_date(d_to)
    if dt < df or (dt - df).days > 365:
        raise ApiError(400, "BAD_RANGE", "Choose a valid date range (max 1 year).")
    days = (dt - df).days + 1
    window = Interval(datetime.combine(df, time.min), datetime.combine(dt + timedelta(days=1), time.min))
    labs = {l["id"]: l for l in conn.execute("SELECT * FROM labs")}
    eqs = [e for e in conn.execute("SELECT * FROM equipment WHERE active=1") if e["lab_id"] in _staff_labs(conn, user)]
    hours = {}
    for e in eqs:
        c = _cfg(labs[e["lab_id"]])
        hours[e["id"]] = days * (datetime.combine(date.min, c.close_time) - datetime.combine(date.min, c.open_time)).total_seconds() / 3600
    ress = [_res(r) for r in conn.execute("SELECT * FROM reservations WHERE start_ts<? AND end_ts>?", (fmt(window.end), fmt(window.start)))]
    rep = utilisation_report(ress, hours, window)
    names = {e["id"]: e["name"] for e in eqs}
    return [{"equipment_id": k, "equipment": names[k], "booked_hours": round(v.booked_hours, 2), "available_hours": round(v.available_hours, 2),
             "utilisation_pct": v.utilisation_pct, "bookings": v.bookings, "cancellations": v.cancellations, "no_shows": v.no_shows}
            for k, v in rep.items()]


def audit_list(conn, user, limit=100):
    require_role(user, *STAFF)
    return [{"actor": r["actor"], "action": r["action"], "at": r["at"], "details": json.loads(r["details"])}
            for r in conn.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (int(limit),))]


# ---------- background work ----------
def run_reminders(conn, transport, now) -> dict:
    rows = conn.execute("SELECT * FROM reminder_jobs WHERE status='Pending'").fetchall()
    jobs = [rem.ReminderJob(r["reservation_id"], parse_dt(r["send_at"]), rem.JobStatus.PENDING, r["attempts"],
                            parse_dt(r["next_attempt_at"]) if r["next_attempt_at"] else None) for r in rows]
    ids = [j.reservation_id for j in jobs]
    if not ids:
        return {"sent": 0, "retry": 0, "failed": 0, "cancelled": 0}
    marks = ",".join("?" * len(ids))
    reservations = {r["id"]: _res(r) for r in conn.execute(f"SELECT * FROM reservations WHERE id IN ({marks})", ids)}
    info = {r["id"]: r for r in conn.execute(
        f"SELECT r.id, u.email, e.name FROM reservations r JOIN users u ON u.id=r.user_id JOIN equipment e ON e.id=r.equipment_id WHERE r.id IN ({marks})", ids)}

    def send(res):
        i = info[res.id]
        transport.send(i["email"], "Reminder: upcoming lab reservation",
                       f"Reminder: {i['name']} at {res.interval.start:%Y-%m-%d %H:%M}.")

    stats = rem.process_due(jobs, reservations, now, send)
    for j in jobs:
        conn.execute("UPDATE reminder_jobs SET status=?, attempts=?, next_attempt_at=? WHERE reservation_id=?",
                     (j.status.value, j.attempts, fmt(j.next_attempt_at) if j.next_attempt_at else None, j.reservation_id))
    return stats


def flush_emails(conn, transport, now, max_attempts=3, backoff=timedelta(minutes=5)) -> dict:
    stats = {"sent": 0, "retry": 0, "failed": 0}
    rows = conn.execute("SELECT * FROM email_jobs WHERE status='Pending' AND (next_attempt_at IS NULL OR next_attempt_at<=?) ORDER BY id", (fmt(now),)).fetchall()
    for r in rows:
        attempts = r["attempts"] + 1
        try:
            transport.send(r["to_email"], r["subject"], r["body"])
        except Exception:
            if attempts >= max_attempts:
                conn.execute("UPDATE email_jobs SET status='Failed', attempts=? WHERE id=?", (attempts, r["id"]))
                stats["failed"] += 1
            else:
                conn.execute("UPDATE email_jobs SET attempts=?, next_attempt_at=? WHERE id=?", (attempts, fmt(now + backoff), r["id"]))
                stats["retry"] += 1
        else:
            conn.execute("UPDATE email_jobs SET status='Sent', attempts=? WHERE id=?", (attempts, r["id"]))
            stats["sent"] += 1
    return stats


def worker_tick(conn, transport, now) -> dict:
    return {"reminders": run_reminders(conn, transport, now), "emails": flush_emails(conn, transport, now)}
