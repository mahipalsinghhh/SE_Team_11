# Demo script: 9 Nov 2026 presentation

About 8 minutes. Everything below works on the code as of 5 Nov. Steps marked **[needs RLRS-x]** only work once
that story is merged; skip them or replace them with a slide if it isn't.

## Before the presentation (do this once, on the presenting laptop)

**Windows (PowerShell)**, two terminals, both in `MIni Project\rlrs` with the venv activated:

Terminal 1, local mail server that prints every email it receives:
```
pip install aiosmtpd
python -m aiosmtpd -n -l localhost:1025
```

Terminal 2, fresh demo data and the app:
```
$env:RLRS_SMTP_HOST="localhost"; $env:RLRS_SMTP_PORT="1025"; $env:RLRS_SMTP_STARTTLS="false"
$env:RLRS_WORKER_INTERVAL_SECONDS="10"
python scripts/seed_demo.py --reset
uvicorn app.main:create_app --factory
```
(macOS: same, with `export RLRS_SMTP_HOST=localhost` etc.)

The seed prints the user ids: **1 Asha (student), 2 Ravi (student), 3 Lab In-charge, 4 Admin**.
Open http://127.0.0.1:8000/docs in the browser. Every request below is done there: open the endpoint, "Try it out",
fill **x-user-id**, Execute.

Rehearse once the day before. Run `seed_demo.py --reset` again just before presenting so the times are fresh.

## The demo

| # | Say | Do | Audience sees |
|---|---|---|---|
| 1 | "RLRS lets students book lab equipment, with conflict checks and automatic reminders. Layered FastAPI app, SQLite, background worker." | Show the folder layout in the README | `api / engine / models / worker / ui` |
| 2 | "It runs and checks its own database." | `GET /health` | `{"status":"ok","database":"ok"}` |
| 3 | **[needs RLRS-2, 7]** "A student signs in and sees the calendar." | Sign in as Asha, open week view | Booked and free slots |
| 4 | **[needs RLRS-6]** "Booking a free slot works; an overlapping one is refused." | Book a free slot, then an overlapping one | 201, then 409 naming the clash |
| 5 | "Reminders go out automatically 2 hours before a slot. Asha has a booking starting in 90 minutes, so the worker sends her reminder on its next run." | Point at Terminal 1 (within ~10 s of start) | Email to asha@example.test, subject "Reminder: your lab booking #3 starts soon", time shown in IST |
| 6 | "Each reminder is sent exactly once, even if the worker runs again or the server restarts." | `GET /api/reminders` with x-user-id **3** | Booking 3 `Sent`, attempts 1. Optionally restart uvicorn and show no second email |
| 7 | "The lab in-charge can block equipment for maintenance. Overlapping bookings are cancelled, reminders stopped and students emailed, all in one transaction." | `POST /api/maintenance-blocks` with x-user-id **3**, body below | 201, `cancelled_reservation_ids: [4]`; Terminal 1 shows the email to ravi@example.test |
| 8 | "The calendar feed now shows that time as maintenance." | `GET /api/equipment/2/schedule` with `from`/`to` around tomorrow | An item with `kind: "maintenance"` |
| 9 | "After a session the in-charge marks attendance. Marking a future booking is refused." | `POST /api/reservations/1/attendance` `{"outcome":"Completed"}` (x-user-id 3), then the same on reservation **3** | 200 Completed, then 409 "before the slot has ended" |
| 10 | "Students can't do staff actions." | Same request with x-user-id **1** | 403 |
| 11 | "Every privileged change is audited, without secrets." | `GET /api/audit` with x-user-id **4** | maintenance.created, reservation.cancelled_by_maintenance, attendance.marked, each with actor |
| 12 | "Utilisation and no-show report for any date range." | `GET /api/reports/utilisation` with today's date range, x-user-id 4 | Booked vs available hours per equipment |
| 13 | "Testing: 69 automated tests, run on Windows, macOS and Linux in CI; integration tests use a real database and a fake clock." | Show `docs/test_evidence_*.txt` and the green GitHub Actions run | 69 passed |
| 14 | "Traceability: every requirement maps to tests, with honest status." | Show `docs/RTM.md` summary table | Pass / Partial / Not built counts |

Body for step 7 (tomorrow's slot for reservation 4: copy its start/end from the seed output or from
`GET /api/equipment/2/schedule`):
```json
{"equipment_id": 2, "start": "<start of reservation 4>Z", "end": "<end of reservation 4>Z", "reason": "Probe replacement"}
```

## If something goes wrong
- No reminder in Terminal 1: check the env vars were set in the same terminal as uvicorn, and that the seed was run
  less than ~30 minutes ago (the reminder is due when the booking is under 2 hours away).
- "Database already has data": run `python scripts/seed_demo.py --reset`.
- Port busy: add `--port 8001`.

## Known limitations to state honestly if asked
- Until RLRS-2 merges, the user is chosen with the `x-user-id` header instead of a login.
- SQLite instead of PostgreSQL (deliberate: same setup on every laptop); concurrency handled with `BEGIN IMMEDIATE`.
- See `docs/RTM.md` for what is not built.
