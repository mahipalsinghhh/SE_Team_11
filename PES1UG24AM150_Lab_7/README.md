# Lab 7: Fuzz Testing with Hypothesis — Train Fare

**Student:** Deepesh M (`PES1UG24AM150`)  
**Assigned Repo:** `https://github.com/SETAPESU26/L6_L7_25_train_fare` (`Lab 7/`)

## Summary of Fuzz Findings & Fixes

| Function | Crashes Found by Hypothesis (Before) | Fix Applied |
|---|---|---|
| `parse_pnr(pnr)` | `IndexError` on `""`, `TypeError` on `None`, unhandled non-10-digit strings | Validated `isinstance(pnr, str)`, stripped whitespace, checked `len(pnr) == 10` and `pnr.isdigit()`, raising `ValueError` on invalid input. |
| `journey_distance(distances_csv)` | `AttributeError` on `None`, empty/single values, negative distance (`distances[-1] - distances[0]`) | Validated non-empty string, >= 2 non-empty CSV tokens, integer parsing, and `total >= 0`, raising `ValueError` on invalid input. |
| `berth_type(seat)` | `AttributeError` on `None`, missing/extra `'-'`, empty coach, non-positive seat number | Validated `isinstance(seat, str)`, single `'-'` split, non-empty coach, and positive integer seat number, raising `ValueError` on invalid input. |

## Verification
- `pytest -v test_train_fare.py`: **3 passed** (100+ generated Hypothesis cases per function, 0 crashes).

## Deliverables
- `train_fare.py` — Fixed implementation with input validation
- `test_train_fare.py` — Hypothesis property-based fuzz tests (`test_parse_pnr_no_crash`, `test_journey_distance_no_crash`, `test_berth_type_no_crash`)
- `fuzz_before_terminal.png` — Terminal screenshot of Hypothesis crashes before fixes
- `fuzz_after_terminal.png` — Terminal screenshot of passing Hypothesis fuzz tests after fixes
