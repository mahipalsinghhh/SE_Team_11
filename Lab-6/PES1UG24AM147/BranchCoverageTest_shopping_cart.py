"""Test cases targeting branch coverage for shopping_cart.py.

Includes the code-coverage tests plus extra cases that force every
decision (if/elif/else, and/or) to evaluate both True and False.
"""
import pytest

from shopping_cart import item_total, cart_discount, shipping_fee


# ---------- item_total ----------

def test_food_item():
    assert item_total("food", 100, 2) == 210


def test_electronics_item():
    assert item_total("electronics", 200, 1) == 236


def test_bulk_discount_applied():
    # qty >= 10 branch taken
    assert item_total("clothing", 50, 12) == 604


def test_no_bulk_discount():
    # qty >= 10 branch not taken
    assert item_total("clothing", 50, 9) == 504


def test_unknown_category():
    # category check True branch
    with pytest.raises(ValueError):
        item_total("toys", 100, 1)


def test_negative_price():
    # price < 0 True (short-circuits the or)
    with pytest.raises(ValueError):
        item_total("food", -50, 1)


def test_zero_quantity():
    # price < 0 False, qty <= 0 True
    with pytest.raises(ValueError):
        item_total("food", 100, 0)


# ---------- cart_discount ----------

def test_discount_high_value_cart():
    # cart_value >= 5000 branch
    assert cart_discount(6000, False, None) == 500


def test_discount_mid_value_cart():
    # cart_value >= 2000 elif branch
    assert cart_discount(2500, False, None) == 200


def test_discount_low_value_cart():
    # else branch, no prime, no coupon
    assert cart_discount(500, False, None) == 0


def test_prime_member_bonus():
    # is_prime True branch
    assert cart_discount(500, True, None) == 100


def test_valid_coupon():
    # coupon == FLAT10 and cart >= 1000, both True
    assert cart_discount(2000, False, "FLAT10") == 400


def test_coupon_below_minimum_cart():
    # coupon matches but cart_value < 1000: second condition False
    assert cart_discount(500, False, "FLAT10") == 0


def test_wrong_coupon_code():
    # coupon != FLAT10: first condition False
    assert cart_discount(6000, False, "SAVE20") == 500


def test_coupon_with_prime_and_big_cart():
    assert cart_discount(6000, True, "FLAT10") == 1200


# ---------- shipping_fee ----------

def test_prime_free_shipping():
    # is_prime True branch
    assert shipping_fee(100, True, False) == 0


def test_free_shipping_above_500():
    # is_prime False, cart_value >= 500 branch
    assert shipping_fee(1000, False, False) == 0


def test_paid_shipping_small_cart():
    # is_prime False, cart_value < 500 else branch
    assert shipping_fee(100, False, False) == 40


def test_express_shipping_non_prime():
    # is_express True, is_prime False inside express block
    assert shipping_fee(100, False, True) == 140


def test_express_shipping_prime():
    # is_express True, is_prime True inside express block
    assert shipping_fee(100, True, True) == 50
