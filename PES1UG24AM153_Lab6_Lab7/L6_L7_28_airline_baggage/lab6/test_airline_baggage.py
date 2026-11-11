import pytest
from airline_baggage import baggage_fee, carry_on_ok, check_in_status

#Example test cases:
def test_within_allowance():
    assert baggage_fee("economy", 10, "domestic", False) == 0

def test_carry_on_ok():
    assert carry_on_ok(5, 1, False) is True

#Write the rest of the test cases so that the code is 90- 100% covered.
