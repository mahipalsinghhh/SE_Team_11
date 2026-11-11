import pytest
from airline_baggage import baggage_fee, carry_on_ok, check_in_status


# ---- baggage_fee ----
def test_within_allowance():
    assert baggage_fee("economy", 10, "domestic", False) == 0

def test_unknown_cabin():
    with pytest.raises(ValueError):
        baggage_fee("first", 10, "domestic", False)

def test_negative_weight():
    with pytest.raises(ValueError):
        baggage_fee("economy", -1, "domestic", False)

def test_member_excess_domestic():
    # allowance 15 + 10 = 25, excess 5 * 20
    assert baggage_fee("economy", 30, "domestic", True) == 100

def test_large_excess_international():
    # allowance 15, excess 25 -> rate 45*2+10 = 100
    assert baggage_fee("economy", 40, "international", False) == 2500


# ---- carry_on_ok ----
def test_carry_on_ok():
    assert carry_on_ok(5, 1, False) is True

def test_carry_on_infant():
    assert carry_on_ok(10, 2, True) is True

def test_carry_on_too_heavy():
    assert carry_on_ok(8, 1, False) is False


# ---- check_in_status ----
def test_check_in_open_with_baggage():
    assert check_in_status(70, True, False) == "open"

def test_check_in_late_no_baggage_international():
    # cutoff 45 + 60 = 105, late window 90..104
    assert check_in_status(95, False, True) == "late"

def test_check_in_closed():
    assert check_in_status(10, True, False) == "closed"
