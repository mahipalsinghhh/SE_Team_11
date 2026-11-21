"""Decision and threshold tests, separate from the statement suite."""
import pytest
from shopping_cart import item_total, cart_discount, shipping_fee


@pytest.mark.parametrize("quantity,expected", [(9, 945), (10, 945), (11, 1039)])
def test_bulk_cutoff(quantity, expected):
    assert item_total("food", 100, quantity) == expected


@pytest.mark.parametrize("category,price,quantity,expected", [
    ("electronics", 99, 1, 116), ("clothing", 100, 1, 112),
    ("food", 0, 1, 0),
])
def test_tax_and_zero_price(category, price, quantity, expected):
    assert item_total(category, price, quantity) == expected


@pytest.mark.parametrize("arguments", [
    ("invalid", 10, 1), ("food", -1, 1),
    ("food", 1, 0), ("food", 1, -1),
])
def test_both_sides_of_validation_or(arguments):
    with pytest.raises(ValueError):
        item_total(*arguments)


@pytest.mark.parametrize("value,expected", [
    (1999, 0), (2000, 200), (4999, 200), (5000, 500),
])
def test_cart_tier_boundaries(value, expected):
    assert cart_discount(value, False, None) == expected


@pytest.mark.parametrize("value,member,code,expected", [
    (999, False, "FLAT10", 0), (1000, False, "FLAT10", 100),
    (1000, False, "OFF10", 0), (1000, True, None, 100),
    (5000, True, "FLAT10", 1100),
])
def test_membership_and_coupon_conditions(value, member, code, expected):
    assert cart_discount(value, member, code) == expected


@pytest.mark.parametrize("value,member,express,expected", [
    (499, False, False, 40), (500, False, False, 0),
    (0, True, False, 0), (499, False, True, 140),
    (500, False, True, 100), (0, True, True, 50),
])
def test_shipping_decision_matrix(value, member, express, expected):
    assert shipping_fee(value, member, express) == expected
