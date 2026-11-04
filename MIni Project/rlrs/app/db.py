"""Database engine and sessions.

SQLite note: every transaction starts with BEGIN IMMEDIATE, which takes the write lock up
front. That makes check-then-insert (booking conflict check, reminder claiming) safe against
concurrent requests and a second worker, as decided in HANDOFF section 3.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url, future=True)
    engine = create_engine(url, future=True, connect_args={"check_same_thread": False, "timeout": 30})

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        dbapi_conn.isolation_level = None  # let us issue BEGIN ourselves
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def utcnow() -> datetime:
    """Naive UTC 'now'. All timestamps are stored as naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt: datetime) -> datetime:
    """Accept aware or naive datetimes from the API; naive input is treated as UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
