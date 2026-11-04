"""Mail transports. Default writes .txt files to ./outbox (a local 'mail catcher'): no real emails.
Set SMTP_HOST (+ SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM) in the environment to use real SMTP."""
import os
import smtplib
import threading
import time
from email.message import EmailMessage
from pathlib import Path


class FileTransport:
    def __init__(self, outbox: str = "outbox"):
        self.dir = Path(outbox)
        self.sent: list[tuple[str, str, str]] = []
        self._lock = threading.Lock()

    def send(self, to: str, subject: str, body: str) -> None:
        with self._lock:
            self.dir.mkdir(parents=True, exist_ok=True)
            name = f"{time.time_ns()}_{len(self.sent)}.txt"
            (self.dir / name).write_text(f"To: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
            self.sent.append((to, subject, body))


class SmtpTransport:
    def __init__(self):
        self.host = os.environ["SMTP_HOST"]
        self.port = int(os.environ.get("SMTP_PORT", "587"))
        self.user = os.environ.get("SMTP_USER")
        self.password = os.environ.get("SMTP_PASSWORD")
        self.sender = os.environ.get("MAIL_FROM", self.user or "rlrs@localhost")

    def send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as s:
            s.starttls()
            if self.user:
                s.login(self.user, self.password or "")
            s.send_message(msg)


def default_transport():
    return SmtpTransport() if os.environ.get("SMTP_HOST") else FileTransport()
