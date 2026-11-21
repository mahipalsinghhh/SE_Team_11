"""Shopping cart helpers with input validation (Lab 7 - fuzz testing)."""

import re

ZONES = {"1": "North", "2": "North", "3": "West", "4": "West",
         "5": "South", "6": "South", "7": "East", "8": "East"}

_ITEM_RE = re.compile(r"^[^:,]+:(\d+)x(\d+)$")
_PROMO_RE = re.compile(r"^OFF(\d{1,3})$")
_PINCODE_RE = re.compile(r"^\d{6}$")


def cart_total(cart):
    """Return the total for a cart string like 'pen:10x2,book:250x1'."""
    if not isinstance(cart, str) or not cart.strip():
        raise ValueError("cart must be a non-empty string")
    total = 0
    for item in cart.split(','):
        match = _ITEM_RE.match(item.strip())
        if match is None:
            raise ValueError(f"bad cart item: {item!r} (expected name:pricexqty)")
        price, qty = match.groups()
        total += int(price) * int(qty)
    return total


def promo_percent(code):
    """Return the discount percent for a promo code like OFF20."""
    if not isinstance(code, str):
        raise ValueError("promo code must be a string")
    match = _PROMO_RE.match(code.strip().upper())
    if match is None:
        raise ValueError(f"bad promo code: {code!r} (expected OFF + digits)")
    percent = int(match.group(1))
    if percent > 100:
        raise ValueError("discount cannot be more than 100%")
    return percent


def delivery_zone(pincode):
    """Return the delivery zone for a 6 digit pincode."""
    if not isinstance(pincode, str) or not _PINCODE_RE.match(pincode.strip()):
        raise ValueError("pincode must be a 6 digit numeric string")
    first = pincode.strip()[0]
    if first not in ZONES:
        raise ValueError(f"no delivery zone for pincodes starting with {first!r}")
    return ZONES[first]


def main():
    print("==== Running cart_total ====")
    user_input = input("Enter cart as name:pricexqty CSV (e.g. pen:10x2,book:250x1): ")
    try:
        print("Cart Total:", cart_total(user_input))
    except ValueError as exc:
        print("Invalid cart:", exc)

    print("\n==== Running promo_percent ====")
    user_input = input("Enter a promo code (e.g. OFF20): ")
    try:
        print("Discount Percent:", promo_percent(user_input))
    except ValueError as exc:
        print("Invalid promo code:", exc)

    print("\n==== Running delivery_zone ====")
    user_input = input("Enter a 6 digit pincode (e.g. 560085): ")
    try:
        print("Delivery Zone:", delivery_zone(user_input))
    except ValueError as exc:
        print("Invalid pincode:", exc)


if __name__ == "__main__":
    main()
