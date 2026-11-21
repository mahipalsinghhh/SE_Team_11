"""Quick smoke checks; the two named suites contain the full cases."""
from shopping_cart import item_total, shipping_fee


def test_single_clothing_item():
    assert item_total("clothing", 200, 1) == 224


def test_member_delivery():
    assert shipping_fee(250, True, False) == 0
