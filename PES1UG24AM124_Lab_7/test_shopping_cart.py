"""Generated invalid inputs, valid data properties and fixed regressions."""
import pytest
from hypothesis import given, settings, strategies as st
from shopping_cart import ZONES, cart_total, promo_percent, delivery_zone

FUZZ_INPUTS = st.one_of(st.none(), st.text(), st.integers(),
                        st.binary(), st.lists(st.integers(), max_size=4))


@settings(max_examples=300, derandomize=True)
@given(FUZZ_INPUTS)
def test_cart_total_no_crash(value):
    try:
        answer = cart_total(value)
    except ValueError:
        return
    assert isinstance(answer, int) and answer >= 0


@settings(max_examples=300, derandomize=True)
@given(FUZZ_INPUTS)
def test_promo_percent_no_crash(value):
    try:
        answer = promo_percent(value)
    except ValueError:
        return
    assert isinstance(answer, int) and 0 <= answer <= 100


@settings(max_examples=300, derandomize=True)
@given(FUZZ_INPUTS)
def test_delivery_zone_no_crash(value):
    try:
        answer = delivery_zone(value)
    except ValueError:
        return
    assert answer in {"North", "South", "East", "West"}


LINE_ITEMS = st.tuples(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12),
    st.integers(min_value=0, max_value=50000),
    st.integers(min_value=0, max_value=40),
)


@settings(max_examples=150, derandomize=True)
@given(st.lists(LINE_ITEMS, min_size=1, max_size=10))
def test_generated_carts_equal_independent_sum(entries):
    text = ",".join(f"{label}:{cost}x{count}" for label, cost, count in entries)
    assert cart_total(text) == sum(cost * count for _, cost, count in entries)


@given(st.integers(min_value=0, max_value=100))
def test_offer_round_trip(amount):
    assert promo_percent(f" off{amount} ") == amount


@given(st.from_regex(r"[1-8][0-9]{5}", fullmatch=True))
def test_supported_prefixes(postal):
    assert delivery_zone(postal) == ZONES[postal[0]]


@given(st.from_regex(r"[09][0-9]{5}", fullmatch=True))
def test_unmapped_prefixes(postal):
    with pytest.raises(ValueError):
        delivery_zone(postal)


@pytest.mark.parametrize("value", ["", "OFF101", "OFF250", "OFF-1", "XOFF20", "OFF20junk"])
def test_bad_offer_regressions(value):
    with pytest.raises(ValueError):
        promo_percent(value)


@pytest.mark.parametrize("value", ["5", "56008", "5600850", "000000", "abcdef", "\u0665\u0666\u0660\u0660\u0668\u0665"])
def test_bad_postal_regressions(value):
    with pytest.raises(ValueError):
        delivery_zone(value)


@pytest.mark.parametrize("value", ["", "pen:10", "pen:1x2:3", "p:-1x2", "p:1x-2", "p:1x2,", " :1x2"])
def test_bad_cart_regressions(value):
    with pytest.raises(ValueError):
        cart_total(value)
