"""Execute each statement, with explicit expected arithmetic."""
import pytest
from shopping_cart import item_total, cart_discount, shipping_fee


@pytest.mark.parametrize("category,price,quantity,expected", [
    ("food", 80, 3, 252),
    ("electronics", 150, 2, 354),
    ("clothing", 75, 10, 756),
])
def test_item_computation(category, price, quantity, expected):
    assert item_total(category, price, quantity) == expected


@pytest.mark.parametrize("arguments", [
    ("books", 40, 1), ("food", -1, 2), ("food", 40, 0),
])
def test_invalid_item(arguments):
    with pytest.raises(ValueError):
        item_total(*arguments)


@pytest.mark.parametrize("value,member,code,expected", [
    (5200, False, None, 500), (2300, False, None, 200),
    (700, False, None, 0), (1200, True, "FLAT10", 220),
])
def test_savings(value, member, code, expected):
    assert cart_discount(value, member, code) == expected


@pytest.mark.parametrize("value,member,express,expected", [
    (500, False, False, 0), (499, False, False, 40),
    (499, False, True, 140), (100, True, True, 50),
])
def test_delivery(value, member, express, expected):
    assert shipping_fee(value, member, express) == expected
