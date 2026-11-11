import math
from hypothesis import given, settings, strategies as st
from airline_baggage import parse_booking, total_weight, tag_label


# ---------- No-crash fuzz tests (random / malformed input) ----------

@settings(max_examples=500)
@given(st.text() | st.none())
def test_parse_booking_no_crash(s):
    try:
        parse_booking(s)
    except Exception as e:
        assert False, f"parse_booking crashed with: {e!r}"


@settings(max_examples=500)
@given(st.text() | st.none())
def test_total_weight_no_crash(s):
    try:
        total_weight(s)
    except Exception as e:
        assert False, f"total_weight crashed with: {e!r}"


@settings(max_examples=500)
@given(st.text() | st.none())
def test_tag_label_no_crash(s):
    try:
        tag_label(s)
    except Exception as e:
        assert False, f"tag_label crashed with: {e!r}"


# ---------- Property tests (valid input must still work correctly) ----------

@given(
    st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=3),
    st.integers(min_value=1, max_value=9999),
    st.integers(min_value=1, max_value=60),
    st.sampled_from("ABCDEF"),
)
def test_parse_booking_valid(airline, flight, row, letter):
    code = f"{airline.lower()}-{flight}-{row}{letter.lower()}"
    assert parse_booking(code) == (airline, flight, letter)


@given(st.lists(st.floats(min_value=0, max_value=100, allow_nan=False), min_size=1, max_size=10))
def test_total_weight_valid(weights):
    csv = ",".join(repr(w) for w in weights)
    assert math.isclose(total_weight(csv), sum(weights), abs_tol=1e-6)


@given(st.floats() | st.text())
def test_total_weight_result_is_finite_and_non_negative(s):
    result = total_weight(str(s))
    assert result is None or (math.isfinite(result) and result >= 0)


@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
)
def test_tag_label_valid(first, last):
    assert tag_label(f"{first} {last}") == f"{first[0].upper()}. {last.upper()}"
