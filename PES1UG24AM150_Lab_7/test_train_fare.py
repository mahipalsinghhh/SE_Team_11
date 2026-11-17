from hypothesis import given, strategies as st
from train_fare import parse_pnr, journey_distance, berth_type


@given(st.text() | st.none())
def test_parse_pnr_no_crash(s):
    try:
        zone, number = parse_pnr(s)
        assert isinstance(zone, int)
        assert isinstance(number, int)
    except ValueError:
        pass


@given(st.text() | st.none())
def test_journey_distance_no_crash(s):
    try:
        dist = journey_distance(s)
        assert isinstance(dist, int)
        assert dist >= 0
    except ValueError:
        pass


@given(st.text() | st.none())
def test_berth_type_no_crash(s):
    try:
        coach, berth = berth_type(s)
        assert isinstance(coach, str) and len(coach) > 0
        assert berth in {"SU", "LB", "MB", "UB", "SL"}
    except ValueError:
        pass
