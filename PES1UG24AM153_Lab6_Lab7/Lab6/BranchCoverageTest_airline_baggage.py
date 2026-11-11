import pytest
from airline_baggage import baggage_fee, carry_on_ok, check_in_status


# ---- baggage_fee: every decision both True and False ----
def test_unknown_cabin():
    with pytest.raises(ValueError):
        baggage_fee("first", 10, "domestic", False)

def test_negative_weight():
    with pytest.raises(ValueError):
        baggage_fee("economy", -1, "domestic", False)

def test_zero_weight_allowed():
    assert baggage_fee("economy", 0, "domestic", False) == 0

def test_within_allowance():
    assert baggage_fee("economy", 10, "domestic", False) == 0

def test_exactly_at_allowance():
    assert baggage_fee("premium", 25, "domestic", False) == 0

def test_member_non_business_gets_bonus():
    # 15 + 10 = 25 allowance -> 25kg is free
    assert baggage_fee("economy", 25, "domestic", True) == 0

def test_member_business_no_bonus():
    # business allowance stays 40 -> 5kg excess * 20
    assert baggage_fee("business", 45, "domestic", True) == 100

def test_non_member_excess_domestic_small():
    assert baggage_fee("economy", 20, "domestic", False) == 5 * 20

def test_excess_international_small():
    assert baggage_fee("economy", 20, "international", False) == 5 * 45

def test_large_excess_domestic():
    # excess 25 -> rate 20*2 = 40, no international surcharge
    assert baggage_fee("economy", 40, "domestic", False) == 25 * 40

def test_large_excess_international():
    # excess 25 -> rate 45*2+10 = 100
    assert baggage_fee("economy", 40, "international", False) == 25 * 100

def test_large_excess_other_route():
    # route not domestic/international -> rate 45*2, no +10
    assert baggage_fee("economy", 40, "regional", False) == 25 * 90

def test_excess_exactly_20_not_doubled():
    assert baggage_fee("economy", 35, "domestic", False) == 20 * 20


# ---- carry_on_ok ----
def test_carry_on_ok():
    assert carry_on_ok(5, 1, False) is True

def test_carry_on_too_many_items():
    assert carry_on_ok(5, 2, False) is False

def test_carry_on_too_heavy():
    assert carry_on_ok(8, 1, False) is False

def test_carry_on_exactly_7kg():
    assert carry_on_ok(7, 1, False) is True

def test_infant_two_items():
    assert carry_on_ok(10, 2, True) is True

def test_infant_three_items():
    assert carry_on_ok(1, 3, True) is False


# ---- check_in_status ----
def test_open_with_baggage_domestic():
    assert check_in_status(60, True, False) == "open"

def test_late_with_baggage_domestic():
    assert check_in_status(50, True, False) == "late"

def test_closed_with_baggage_domestic():
    assert check_in_status(44, True, False) == "closed"

def test_open_no_baggage_domestic():
    assert check_in_status(45, False, False) == "open"

def test_late_no_baggage_domestic():
    assert check_in_status(30, False, False) == "late"

def test_closed_no_baggage_domestic():
    assert check_in_status(29, False, False) == "closed"

def test_open_with_baggage_international():
    assert check_in_status(120, True, True) == "open"

def test_late_no_baggage_international():
    assert check_in_status(95, False, True) == "late"

def test_closed_international():
    assert check_in_status(60, True, True) == "closed"
