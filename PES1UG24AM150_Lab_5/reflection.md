# Lab 5 — Reflection (`PES1UG24AM150`)

**Q1. What did you learn about static code analysis?**

Static code analysis inspects source code without executing it, catching security vulnerabilities, subtle runtime risks, and maintainability issues early. Even though `tower_maintenance.py` ran and printed the expected output (`['Ridge-A'] high 2 1`), static analysis revealed a SQL injection flaw, unsafe `pickle` deserialization, a hardcoded password, and an unchecked `None` dereference.

**Q2. Which issues found by the tools were most surprising or valuable?**

The most valuable findings were the `B608` SQL injection in `addTower` (using `%` string formatting in `conn.execute`) and the `B301` unsafe `pickle` usage in `snapshot()`. Fixing the `fetchone()` null-check in `risk_level` and replacing `global service_count` with a `TowerTracker` class also made the code much safer and easier to test.

**Q3. How do Pylint, Bandit and Flake8 differ in what they catch?**

- **Bandit** focuses on security vulnerabilities (SQL injection `B608`, unsafe `pickle` `B301`/`B403`, hardcoded passwords `B105`).
- **Pylint** evaluates code quality, design, and potential bugs (naming conventions, docstrings, `global` usage `W0603`, broad exception catching `W0718`, unnecessary `else` `R1705`).
- **Flake8** enforces PEP 8 style rules (line length `E501`, blank lines `E303`, operator spacing `E225`).

**Q4. How will you apply static analysis in your future projects?**

I will run `pylint`, `bandit`, and `flake8` continuously during development (via editor integration, pre-commit hooks, or GitHub Actions CI) so security and style issues are prevented before code is merged, rather than fixed at the end.
