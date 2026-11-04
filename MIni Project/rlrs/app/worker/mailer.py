"""Mailers. Anything with send(to, subject, body) works; tests pass a fake one."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.config import Settings

log = logging.getLogger("rlrs.mail")


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleMailer:
    """Development default when RLRS_SMTP_HOST is unset: logs the email instead of sending it."""

    def send(self, to: str, subject: str, body: str) -> None:
        log.warning("EMAIL (console, not sent) to=%s subject=%s\n%s", to, subject, body)


class SmtpMailer:
    def __init__(self, settings: Settings):
        self.s = settings

    def send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.s.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=15) as smtp:
            if self.s.smtp_starttls:
                smtp.starttls()
            if self.s.smtp_user:
                smtp.login(self.s.smtp_user, self.s.smtp_password or "")
            smtp.send_message(msg)


def mailer_from_settings(settings: Settings) -> Mailer:
    return SmtpMailer(settings) if settings.smtp_host else ConsoleMailer()
