# Lab 6: Code and Branch Coverage Analysis — Train Fare

**Student:** Deepesh M (`PES1UG24AM150`)  
**Assigned Repo:** `https://github.com/SETAPESU26/L6_L7_25_train_fare` (`Lab 6/`)

## Results Summary

| Metric | Test File | Coverage (`train_fare.py`) |
|---|---|---|
| Code (Statement) Coverage | `CodeCoverageTest_train_fare.py` | **100%** (31/31 stmts) |
| Branch Coverage | `BranchCoverageTest_train_fare.py` | **100%** (31/31 stmts, 22/22 branches) |

## Commands Used

```bash
# Code (Line) Coverage
coverage run -m pytest CodeCoverageTest_train_fare.py
coverage report -m

# Branch Coverage
coverage run --branch -m pytest BranchCoverageTest_train_fare.py
coverage report -m
```

## Deliverables
- `train_fare.py` — Module under test
- `test_train_fare.py` — Starter test file
- `CodeCoverageTest_train_fare.py` — Unit tests achieving 100% statement coverage
- `BranchCoverageTest_train_fare.py` — Unit tests achieving 100% branch coverage
- `code_coverage_terminal.png` — Terminal output screenshot for code coverage
- `branch_coverage_terminal.png` — Terminal output screenshot for branch coverage
