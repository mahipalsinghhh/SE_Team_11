# Demo script (9 Nov, about 8 minutes)

**Before:** `cd "MIni Project/rlrs"`, delete `rlrs.db` and `outbox/` for a clean start, run `python -m rlrs_app.server --seed`, open http://127.0.0.1:8000 in two browser windows (one normal, one private).

1. **Problem and design (1 min).** Students cannot see free equipment slots, double bookings happen, reminders are manual. Show `docs/diagrams` (component + sequence). Say: scheduling logic is a pure module with 37 unit tests; the web layer is built on it.
2. **Sign in as student1** (window A). Show the week calendar: Free / Yours / Booked / Maintenance / Past, each with a text label.
3. **Book a slot** on the Oscilloscope (click a green slot, choose duration, Reserve). Message: confirmed. Open `outbox/`: the confirmation email file.
4. **Conflict detection.** Sign in as student2 (window B). The same slot shows Booked. Pick a different slot and try a 3-hour booking: rejected with the rule message (max 120 min). Try a time outside 09:00-18:00 via a past slot: rejected.
5. **Approval flow.** student2 books the 3D Printer (needs approval): status Pending. Sign in as incharge in window A, Manage, Approve (or Reject with a reason).
6. **Maintenance.** As incharge, block the Oscilloscope over student1's slot: the booking is cancelled, student1's email is in `outbox/`, the calendar shows Maintenance.
7. **Cancel and reuse.** student2 cancels their booking; the slot is free again. (Cancelling within 60 min of the start is refused.)
8. **Staff tools (1 min).** Attendance marking for finished slots, Reports (utilisation, cancellations, no-shows), audit log (no passwords in it).
9. **Evidence (1 min).** `docs/test_evidence_2026-11-05.txt`: 67 tests passed incl. a test where 10 parallel requests for one slot give exactly one booking; 9/9 browser steps.
10. **Honest limits (30 s).** Stdlib stack instead of FastAPI; lab-local time; real SMTP and Windows/macOS runs not yet verified; no HTTPS.

**If something breaks:** show `python -m pytest -v` output and the screenshots in `tests/ui/screenshots/`.
