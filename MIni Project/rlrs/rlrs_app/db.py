"""SQLite schema and connection helper."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK(role IN ('Student','LabInCharge','Admin')), pw_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(
  token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS labs(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, incharge_id INTEGER REFERENCES users(id),
  open_time TEXT NOT NULL DEFAULT '09:00', close_time TEXT NOT NULL DEFAULT '18:00',
  slot_minutes INTEGER NOT NULL DEFAULT 30, max_duration INTEGER NOT NULL DEFAULT 120,
  advance_days INTEGER NOT NULL DEFAULT 14, max_active INTEGER NOT NULL DEFAULT 3);
CREATE TABLE IF NOT EXISTS equipment(
  id INTEGER PRIMARY KEY, lab_id INTEGER NOT NULL REFERENCES labs(id), name TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
  requires_approval INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  remote_info TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS reservations(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
  equipment_id INTEGER NOT NULL REFERENCES equipment(id),
  start_ts TEXT NOT NULL, end_ts TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Pending','Confirmed','Cancelled','Rejected','Completed','NoShow')),
  created_at TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS ix_res_eq ON reservations(equipment_id, start_ts, end_ts);
CREATE TABLE IF NOT EXISTS maintenance(
  id INTEGER PRIMARY KEY, equipment_id INTEGER NOT NULL REFERENCES equipment(id),
  start_ts TEXT NOT NULL, end_ts TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS reminder_jobs(
  id INTEGER PRIMARY KEY, reservation_id INTEGER NOT NULL UNIQUE REFERENCES reservations(id),
  send_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
  attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT);
CREATE TABLE IF NOT EXISTS email_jobs(
  id INTEGER PRIMARY KEY, to_email TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Pending', attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, at TEXT NOT NULL,
  details TEXT NOT NULL DEFAULT '{}');
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=15, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
