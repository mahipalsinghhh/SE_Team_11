"""Test cases targeting code (line) coverage for shopping_cart.py."""
import pytest

from shopping_cart import item_total, cart_discount, shipping_fee


# ---------- item_total ----------

def test_food_item():
    assert item_total("food", 100, 2) == 210


def test_electronics_item():
    assert item_total("electronics", 200, 1) == 236


def test_bulk_discount_applied():
    # qty >= 10 gets 10% off before GST
    assert item_total("clothing", 50, 12) == 604


def test_unknown_category():
    with pytest.raises(ValueError):
        item_total("toys", 100, 1)


def test_negative_price():
    with pytest.raises(ValueError):
        item_total("food", -50, 1)


def test_zero_quantity():
    with pytest.raises(ValueError):
        item_total("food", 100, 0)


# ---------- cart_discount ----------

def test_discount_high_value_cart():
    assert cart_discount(6000, False, None) == 500


def test_discount_mid_value_cart():
    assert cart_discount(2500, False, None) == 200


def test_discount_low_value_cart():
    assert cart_discount(500, False, None) == 0


def test_prime_member_bonus():
    assert cart_discount(500, True, None) == 100


def test_valid_coupon():
    # 200 (cart >= 2000) + 10% of 2000
    assert cart_discount(2000, False, "FLAT10") == 400


def test_coupon_with_prime_and_big_cart():
    # 500 + 100 (prime) + 600 (10% of 6000)
    assert cart_discount(6000, True, "FLAT10") == 1200


# ---------- shipping_fee ----------

def test_free_shipping():
    assert shipping_fee(1000, False, False) == 0


def test_prime_free_shipping():
    assert shipping_fee(100, True, False) == 0


def test_paid_shipping_small_cart():
    assert shipping_fee(100, False, False) == 40


def test_express_shipping():
    assert shipping_fee(100, False, True) == 140


def test_express_prime_discount():
    assert shipping_fee(100, True, True) == 50
