"""SQLAlchemy ORM models (data layer). Timestamps are naive UTC; ranges are half-open [start, end).

Status values are the strings from rlrs_core.types.Status, so the engine and DB agree.
"""
from __future__ import annotations

from datetime import datetime, time
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from rlrs_core.types import Status


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    STUDENT = "student"
    LAB_INCHARGE = "lab_incharge"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    role: Mapped[str] = mapped_column(String(20), default=Role.STUDENT.value)


class Lab(Base):
    __tablename__ = "labs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    open_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    close_time: Mapped[time] = mapped_column(Time, default=time(18, 0))
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    max_duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    advance_days: Mapped[int] = mapped_column(Integer, default=14)
    max_active_per_user: Mapped[int] = mapped_column(Integer, default=3)
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="lab")


class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"))
    name: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    lab: Mapped[Lab] = relationship(back_populates="equipment")


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))
    start_utc: Mapped[datetime] = mapped_column(DateTime)
    end_utc: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(12), default=Status.CONFIRMED.value)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    user: Mapped[User] = relationship()
    equipment: Mapped[Equipment] = relationship()
    __table_args__ = (Index("ix_reservation_equipment_start", "equipment_id", "start_utc"),)


class MaintenanceBlock(Base):
    __tablename__ = "maintenance_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))
    start_utc: Mapped[datetime] = mapped_column(DateTime)
    end_utc: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str] = mapped_column(String(300), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ReminderJob(Base):
    """One reminder per reservation (unique), so it can never be planned twice."""
    __tablename__ = "reminder_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), unique=True)
    send_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(12), default="Pending")  # Pending/Sending/Sent/Failed/Cancelled
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(300), nullable=True)


class OutboxEmail(Base):
    """Notification emails written inside the business transaction, sent after commit.
    Lets a maintenance block cancel bookings and queue the emails atomically."""
    __tablename__ = "outbox_emails"
    id: Mapped[int] = mapped_column(primary_key=True)
    to: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="Pending")  # Pending/Sending/Sent/Failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(300), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
