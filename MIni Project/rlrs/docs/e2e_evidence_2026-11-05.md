# End-to-end run, 5 Nov 2026 (01:36 IST)

Real `uvicorn` server, real background worker (APScheduler, 3-second interval) and a real SMTP
server (`python -m aiosmtpd`, delivering to a Maildir). Data from `scripts/seed_demo.py`.
Linux, Python 3.13. Not yet repeated on Windows/macOS (CI matrix covers the automated tests).

| Step | Request | Result |
|---|---|---|
| Health | `GET /health` | `{"status":"ok","database":"ok"}` |
| RLRS-13 mark finished booking | `POST /api/reservations/1/attendance {"outcome":"Completed"}` as in-charge | 200, status `Completed` |
| RLRS-13 mark future booking | `POST /api/reservations/3/attendance` | 409 "Cannot mark attendance before the slot has ended." |
| RLRS-12 maintenance block over booking 4 | `POST /api/maintenance-blocks` (Logic Analyser, reason "Probe replacement") | 201, `cancelled_reservation_ids: [4]` |
| RLRS-10 reminders after one worker cycle | `GET /api/reminders` | booking 3: `Sent`, attempts 1; booking 4: `Cancelled` (maintenance) |
| RLRS-14 report | `GET /api/reports/utilisation` | per-equipment rows returned (booked, available, %, counts) |
| RLRS-13 audit | `GET /api/audit` as admin | `maintenance.created`, `reservation.cancelled_by_maintenance`, `attendance.marked`, each with actor |

Emails received by the SMTP server:

| To | Subject |
|---|---|
| ravi@example.test | Your lab booking #4 was cancelled for maintenance |
| asha@example.test | Reminder: your lab booking #3 starts soon |

Server log: no errors or tracebacks.

Automated tests the same day: 69 passed (`test_evidence_2026-11-05.txt`).
