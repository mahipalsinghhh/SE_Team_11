# Lab 7 - Fuzz Testing: Bugs Found

Program: `shopping_cart.py`
Tool: Hypothesis (property-based fuzzing) with pytest

The three `no_crash` fuzz tests throw random text and `None` at each function. On the buggy code, Hypothesis found 4 failing tests with these minimal crashing inputs:

| # | Function | Crashing input | Exception | Root cause | Fix |
|---|----------|---------------|-----------|------------|-----|
| 1 | `cart_total` | `None` | `AttributeError: 'NoneType' object has no attribute 'split'` | No type/null check before `cart.split(',')` | Reject non-string / empty input with a clear `ValueError` |
| 2 | `cart_total` | `"pen:10"` (no `x`), `"a:1x2:3"` | raw `ValueError` from tuple unpacking | `item.split(':')` assumed exactly 2 parts, `rest.split('x')` assumed exactly 2 | Validate each item against a `name:pricexqty` pattern, raise one clear error |
| 3 | `promo_percent` | `""` | `IndexError: list index out of range` | `split('OFF')[1]` assumes "OFF" is present | Match `^OFF\d{1,3}$` and reject anything else |
| 4 | `promo_percent` | `None` | `AttributeError: 'NoneType' object has no attribute 'upper'` | No type check before `.upper()` | Same pattern check after an `isinstance` check |
| 5 | `promo_percent` | `"OFF250"` | returns 250 (silent bad data) | No range check on the percent | Reject anything above 100 |
| 6 | `delivery_zone` | `"0"` | `KeyError: '0'` | `ZONES[pincode[0]]` assumes the first digit is in the table | Check the first digit is a known zone, else `ValueError` |
| 7 | `delivery_zone` | `""` | `IndexError: string index out of range` | `pincode[0]` on an empty string | Require a 6 digit numeric string before indexing |
| 8 | `delivery_zone` | `None` | `TypeError: 'NoneType' object is not subscriptable` | No type check | Same `isinstance` + format check |
| 9 | `delivery_zone` | `"5"` (1 digit) | returns `"South"` (silent bad data) | No length check, so short or long pincodes slip through | Regex `^\d{6}$` enforces exactly 6 digits |

## Result

- Before: `4 failed, 3 passed` - the fuzz tests crash the buggy code (see `fuzz_before.txt` / `fuzz_before.png`)
- After: `7 passed` - the fixed code either returns a sane value or raises a clean `ValueError` for every random input Hypothesis generated (see `fuzz_after.txt` / `fuzz_after.png`)

## How to run

```bash
pip install hypothesis pytest
pytest test_shopping_cart.py -v
```
