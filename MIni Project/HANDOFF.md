# RLRS Team 11: Context Handoff

*Written 31 Oct 2026 for Lakshya, Deepesh, Venkat and anyone (or any AI assistant) picking this project up. Everything below reflects the real state of the project on that date.*

## 1. The project
**Remote Lab Reservation System (RLRS)**: a booking portal where students reserve lab-equipment timeslots, see calendar availability and get automated email reminders. It combines calendar UI widgets, RESTful endpoints and a scheduling engine with conflict detection.
Course: Software Engineering, CSE(AIML), PES University. Mini-project, 4 members.

| Member | SRN | Role |
|---|---|---|
| Mahipal Singh | PES1UG24AM153 | **Team leader**, Windows |
| Deepesh M (Jira: `mdeepesh2006`) | PES1UG24AM150 | macOS |
| Venkat Kushal | PES1UG24AM124 | Windows. **Has not yet accepted the Jira invite** |
| Lakshya Budhauliya | PES1UG24AM147 | Windows |

**Deadlines:** Sprint 1 27-31 Oct (closed). Sprint 2 2-7 Nov. **Presentation Mon 9 Nov 2026.**

## 2. Where things live
- **Repo:** https://github.com/mahipalsinghhh/SE_Team_11 (code goes in `MIni Project/`; the folder name has that spelling, keep it)
- **Jira:** https://singhmahipal1312.atlassian.net/jira/software/projects/RLRS/boards/36/backlog (project key `RLRS`)
- **Documents:** `MIni Project/Document/` holds the SRS, SAD and Test Plan drafts (30-31 Oct).

## 3. Decisions already made (do not reopen without telling Mahipal)
- **Stack (recommended, approved by Mahipal):** FastAPI, SQLAlchemy, **SQLite**, APScheduler, FullCalendar on a plain HTML/JS front end, pytest. No PostgreSQL: SQLite runs the same on Windows and Mac. (The SRS/SAD say PostgreSQL is preferred: update them in RLRS-15. The concurrency guard becomes one locked transaction (`BEGIN IMMEDIATE`) around check-then-insert.)
- **Architecture:** layered modular monolith: browser UI, REST API, scheduling engine, data layer, reminder worker.
- **Scope:** Must = auth, labs/equipment, calendar, reservation with conflict detection and rules, cancel, confirmation and reminder emails. Should = approval, maintenance, attendance, audit. Could = utilisation report. If time runs out, drop in this order: RLRS-14, 13, 12, 11.
- **Time zone/storage:** timestamps stored in UTC, shown in the lab's time zone. Time ranges are half-open `[start, end)`: back-to-back bookings are allowed.

## 4. Jira state
15 stories, **74 story points** total. **Sprint 1 was closed with 0 stories done** (the project only started on 31 Oct), and all 15 stories were carried into **Sprint 2 ("Sprint 2 - Build and Test"), which has not been started yet.** Mahipal starts it on 2 Nov.

| Owner | Stories (points) |
|---|---|
| **Lakshya** | RLRS-1 skeleton and CI (3), RLRS-4 conflict detection (8), RLRS-5 booking rules (5), RLRS-6 reservation API (5), RLRS-11 approval workflow (3) |
| **Deepesh** | RLRS-2 sign-in and roles (5), RLRS-3 lab and equipment management (5), RLRS-7 calendar UI (8), RLRS-8 booking form, My Reservations, cancel (5), RLRS-9 confirmation emails (3) |
| **Mahipal** | RLRS-10 reminder worker (8), RLRS-12 maintenance blocks (5), RLRS-13 attendance and audit (3), RLRS-14 utilisation report (3), RLRS-15 integration testing and docs (5) |
| **Venkat** | Nothing yet. Once he accepts, Mahipal will move some stories to him. |

Every story has acceptance criteria and links to SRS requirement IDs and Test Plan case IDs in its description. **Read the story before coding it.**

## 5. What is actually built (verified)
In `MIni Project/rlrs/` (pure Python, no web/DB dependencies): `conflict.py`, `rules.py`, `reminders.py`, `maintenance.py`, `attendance.py`, `audit.py`, `report.py`, with **37 unit tests, all passing** (`rlrs/docs/test_evidence_unit_2026-10-31.txt`). UML sources (PlantUML: use case, class, 2 sequence, activity, component) are in `rlrs/docs/diagrams/`.
This is the *logic core* behind RLRS-4, 5, 10, 12, 13 and 14, so **those Jira stories are still To Do** (see their comments). The API, database and UI do not exist.

**Not built / not verified:** FastAPI app, SQLAlchemy models/SQLite, auth, equipment CRUD, reservation endpoint, calendar UI, SMTP sending, APScheduler wiring, integration tests, CI has never run on GitHub, UML not yet rendered or syntax-checked.

## 6. What each person does next
- **Lakshya (first, today/Sun 1 Nov):** RLRS-1, the project skeleton. Others are blocked on it. Wire `rlrs_core` into the app instead of rewriting the logic. Push by Sunday 1 Nov.
- **Deepesh:** RLRS-2 and RLRS-3 once the skeleton is on `main`; the calendar UI (RLRS-7) after the API exists.
- **Lakshya (after skeleton):** RLRS-6 should call `rlrs_core.rules.validate_booking` then `conflict.find_conflicts` inside one locked transaction (see `03_sequence_booking.puml`).
- **Mahipal:** wire RLRS-10/12/13/14 into the API once the database exists; then RLRS-15.
- **Venkat:** accept the Jira invite, clone the repo, run the tests; Mahipal will assign stories.

## 7. Git workflow (required)
Branch from `main`, one branch per Jira story, Jira key in branch and commit, open a Pull Request, get one review, merge. (The repo README currently says "push to main"; Mahipal will update it. Use PRs.)
```
git clone https://github.com/mahipalsinghhh/SE_Team_11.git
cd SE_Team_11
git switch main && git pull origin main
git switch -c feature/RLRS-1-project-skeleton
# ...work, then:
git add -A
git commit -m "feat(RLRS-1): add FastAPI skeleton and CI"
git push -u origin feature/RLRS-1-project-skeleton
```
Then open a Pull Request on GitHub targeting `main`.

**Set up Python and run the existing tests**
- *Windows (PowerShell):* `cd "MIni Project\rlrs"; py -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt; python -m pytest -v`
- *macOS (Terminal):* `cd "MIni Project/rlrs" && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python -m pytest -v`

## 8. Rules (from the team workflow)
1. Never mark a Jira story **Done** because code was committed. Done = acceptance criteria verified. Keep real test output as evidence.
2. Never claim a feature works unless it was run and checked. Do not invent test results in the documents.
3. No secrets or real student emails in the repo. SMTP settings come from environment variables; use a local mail catcher in development.
4. Keep Jira, GitHub, UML, code and the SRS/SAD/Test Plan in sync. At the end (RLRS-15), update the documents to match what was really built.
5. Prefer a small working demo over extra features.

## 9. Known issues to fix
- Test Plan v1.0 Sprint 1 row claims tests for implemented stories in Sprint 1: not true. Correct it to match reality.
- Test Plan roles table still says "fill in name".
- SRS/SAD mention PostgreSQL; the chosen stack is SQLite.
- Repo README: says "push to main", lists folders `lab_01`/`mini_project` that don't exist, and the project title in the course sheet has a typo ("Systemzzz"); use "Remote Lab Reservation System".
- The repo has one fork. Everyone should clone the main repo directly (Mahipal adds collaborators).

## 10. Open questions for Mahipal
- Does the instructor accept the compressed Sprint 1 (planning/design only)? Ask if an extension is possible.
- Should each member write their own stories' code (likely yes), or may the logic core in `rlrs/` be reused?
