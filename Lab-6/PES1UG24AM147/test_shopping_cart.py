import pytest
from shopping_cart import item_total, cart_discount, shipping_fee

#Example test cases:
def test_food_item():
    assert item_total("food", 100, 2) == 210

def test_free_shipping():
    assert shipping_fee(1000, False, False) == 0

#Write the rest of the test cases so that the code is 90- 100% covered.
