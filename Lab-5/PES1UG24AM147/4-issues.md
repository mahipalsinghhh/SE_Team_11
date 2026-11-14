# Lab 5 - Static Code Analysis: Issue Table

Program: `bike_share_stations.py` (Bike-Share Station Manager)
Tools: Pylint, Bandit, Flake8

| # | Issue | Type | Line(s) | Description | Fix Approach |
|---|-------|------|---------|-------------|--------------|
| 1 | SQL injection vector (B608) | Security - Medium | 9 | INSERT query built by string concatenation of `name`, `capacity`, `bikes` | Switched to a parameterized query with `?` placeholders |
| 2 | Mutable default argument (W0102) | Bug - High | 8 | `log=[]` is shared across every call of `addStation`, so names leak between calls | Default changed to `None`, new list created inside the function |
| 3 | Missing-station crash / wrong None check (C0121, E711) | Bug - High | 40 | `row[0] == None` compares the column instead of the row; `hasBikes` crashes with TypeError when the station id does not exist because `fetchone()` returns None | Check `row is None` first and return False |
| 4 | Insecure random for unlock PIN (B311) | Security - Low | 21 | `random.randint` is not suitable for security purposes | Replaced with `secrets.randbelow(9000) + 1000` |
| 5 | try / except / pass (B110, W0718) | Bug - Medium | 31-35 | Broad `except Exception: pass` silently swallows every database error | Catch `sqlite3.Error` specifically and print a message |
| 6 | Inconsistent return statements (R1710) | Code quality | 14-19 | `rentBike` returns True on success but an implicit None on failure | Explicit `return False` on the failure path |
| 7 | Unused variable (W0612, F841) | Code quality | 27 | `summary = len(stations)` assigned but never used | Removed |
| 8 | Naming, docstrings and formatting (C0103, C0114, C0116, C0301, C0303, E501, W291) | Style | many | camelCase function names, missing docstrings, lines over the limit, trailing whitespace | Renamed to snake_case, added module and function docstrings, wrapped long lines, removed trailing whitespace |

## Scores

- Pylint: 3.89/10 (before) -> 10.00/10 (after)
- Bandit: 3 issues (before) -> 0 issues (after)
- Flake8: 10 issues (before) -> 0 issues (after)
