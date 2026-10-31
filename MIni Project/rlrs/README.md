# RLRS core (Remote Lab Reservation System)

Framework-independent domain logic from the SAD's layered design. Pure Python 3.10+, no web, DB or email dependencies.

| Module | Jira | What it does |
|---|---|---|
| `rlrs_core/conflict.py` | RLRS-4 | Half-open interval conflict detection (reservations + maintenance) |
| `rlrs_core/rules.py` | RLRS-5 | Booking rules (hours, grid, window, duration, per-user limits) |
| `rlrs_core/reminders.py` | RLRS-10 | Reminder planning, exactly-once delivery, retry/backoff (fake clock) |
| `rlrs_core/maintenance.py` | RLRS-12 | Maintenance block cancels overlapping reservations |
| `rlrs_core/attendance.py`, `audit.py` | RLRS-13 | Completed/No-show marking; audit log with secret redaction |
| `rlrs_core/report.py` | RLRS-14 | Utilisation and no-show report |

## Run the tests (Windows / macOS / Linux)
```
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
```
Result recorded on 31 Oct 2026: 37 passed (`docs/test_evidence_unit_2026-10-31.txt`).

## Not built yet
FastAPI endpoints, SQLAlchemy/SQLite persistence, APScheduler wiring, SMTP sending, the FullCalendar UI, authentication. These are the remaining parts of RLRS-1/2/3/6/7/8/9 and the wiring for RLRS-10 to 14. Nothing here has been tested against a real database, SMTP server or browser.

UML sources (PlantUML) are in `docs/diagrams/`. They have not been rendered or syntax-checked yet.
