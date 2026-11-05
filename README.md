# SE_Team_11

Team repository for Software Engineering coursework: Dept. of CSE(AIML), PES University. Used for lab submissions and the semester mini-project.

## Team

| Name               | SRN           | Role        |
|:-------------------|:--------------|:------------|
| Mahipal Singh      | PES1UG24AM153 | Team leader |
| Deepesh M          | PES1UG24AM150 |             |
| Venkat Kushal      | PES1UG24AM124 |             |
| Lakshya Budhauliya | PES1UG24AM147 |             |

## Repository Structure

```
SE_Team_11/
├── Lab 1/ Lab 2/ Lab 3/ Lab-4/     # individual lab submissions
├── MIni Project/
│   ├── HANDOFF.md                  # current project state, owners, next steps: read first
│   ├── Document/                   # SRS, SAD, Test Plan
│   └── rlrs/                       # code, tests, UML (rlrs/docs/diagrams)
└── README.md
```

## Mini-Project: Remote Lab Reservation System (RLRS)

- **Problem statement:** A booking portal for students to reserve lab equipment timeslots, view calendar availability, and receive automated email reminders. It combines calendar UI widgets, RESTful endpoints, and a scheduling engine with conflict detection.
- **Stack:** standard-library Python + SQLite + plain HTML/JS calendar (see `MIni Project/rlrs/README.md`), pytest, GitHub Actions.
- **Status:** working app with 67 passing tests and a passing browser test, run on Linux only: see `MIni Project/HANDOFF.md` for what is verified and what is not.
- **Jira:** project key `RLRS` (Scrum board). Sprint 1: 27-31 Oct. Sprint 2: 2-7 Nov. Presentation: 9 Nov 2026.

Run the tests: `cd "MIni Project/rlrs"`, create a virtual environment, `pip install -r requirements.txt`, `python -m pytest -v`.

## Contribution Guidelines

- Do not commit feature work directly to `main`. Branch from the latest `main`: `git switch main && git pull origin main && git switch -c feature/RLRS-<n>-short-name`.
- Put the Jira key in branch names and commits, e.g. `feat(RLRS-6): add reservation endpoint`.
- Open a Pull Request into `main` and get one teammate's review before merging.
- Add or update tests when behaviour changes. Never commit secrets or real student contact details.
- Mark a Jira story Done only after its acceptance criteria have been verified.

## Course Info

- **Course:** Software Engineering
- **Department:** CSE(AIML), PES University
