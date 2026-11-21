"""Lab 7 fuzz tests for shopping_cart.py using Hypothesis."""

import pytest
from hypothesis import given, strategies as st

from shopping_cart import ZONES, cart_total, delivery_zone, promo_percent

# --- Required fuzz tests: whatever text/None we throw in, the functions
# must never blow up with an unexpected exception. They either return a
# sane value or reject the input cleanly with ValueError. ---


@given(st.text() | st.none())
def test_cart_total_no_crash(s):
    try:
        result = cart_total(s)
    except ValueError:
        return  # input rejected cleanly
    assert isinstance(result, int)
    assert result >= 0


@given(st.text() | st.none())
def test_promo_percent_no_crash(s):
    try:
        result = promo_percent(s)
    except ValueError:
        return  # input rejected cleanly
    assert isinstance(result, int)
    assert 0 <= result <= 100


@given(st.text() | st.none())
def test_delivery_zone_no_crash(s):
    try:
        result = delivery_zone(s)
    except ValueError:
        return  # input rejected cleanly
    assert result in ZONES.values()


# --- Property tests on valid-looking inputs ---

cart_item = st.builds(
    lambda name, price, qty: (name, price, qty),
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), min_size=1, max_size=10),
    price=st.integers(min_value=0, max_value=100000),
    qty=st.integers(min_value=1, max_value=100),
)


@given(st.lists(cart_item, min_size=1, max_size=8))
def test_cart_total_matches_sum(items):
    cart = ",".join(f"{name}:{price}x{qty}" for name, price, qty in items)
    expected = sum(price * qty for _, price, qty in items)
    assert cart_total(cart) == expected


@given(st.integers(min_value=0, max_value=100))
def test_promo_percent_valid_codes(percent):
    assert promo_percent(f"OFF{percent}") == percent


@given(st.from_regex(r"[1-8][0-9]{5}", fullmatch=True))
def test_delivery_zone_valid_pincodes(pincode):
    assert delivery_zone(pincode) == ZONES[pincode[0]]


@given(st.from_regex(r"[09][0-9]{5}", fullmatch=True))
def test_delivery_zone_unknown_first_digit_rejected(pincode):
    with pytest.raises(ValueError):
        delivery_zone(pincode)
