"""Configuration from environment variables only. Nothing secret lives in the repo."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./rlrs.db"
    smtp_host: str | None = None          # unset -> emails are printed to the console (dev)
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "rlrs@localhost"
    smtp_starttls: bool = True
    reminder_lead_minutes: int = 120
    worker_enabled: bool = True
    worker_interval_seconds: int = 60
    max_send_attempts: int = 3
    retry_backoff_minutes: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("RLRS_DATABASE_URL", cls.database_url),
            smtp_host=os.getenv("RLRS_SMTP_HOST") or None,
            smtp_port=int(os.getenv("RLRS_SMTP_PORT", cls.smtp_port)),
            smtp_user=os.getenv("RLRS_SMTP_USER") or None,
            smtp_password=os.getenv("RLRS_SMTP_PASSWORD") or None,
            smtp_from=os.getenv("RLRS_SMTP_FROM", cls.smtp_from),
            smtp_starttls=_bool("RLRS_SMTP_STARTTLS", cls.smtp_starttls),
            reminder_lead_minutes=int(os.getenv("RLRS_REMINDER_LEAD_MINUTES", cls.reminder_lead_minutes)),
            worker_enabled=_bool("RLRS_WORKER_ENABLED", cls.worker_enabled),
            worker_interval_seconds=int(os.getenv("RLRS_WORKER_INTERVAL_SECONDS", cls.worker_interval_seconds)),
            max_send_attempts=int(os.getenv("RLRS_MAX_SEND_ATTEMPTS", cls.max_send_attempts)),
            retry_backoff_minutes=int(os.getenv("RLRS_RETRY_BACKOFF_MINUTES", cls.retry_backoff_minutes)),
        )
