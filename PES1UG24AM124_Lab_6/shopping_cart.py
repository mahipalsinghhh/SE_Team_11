"""Cart arithmetic used by the line- and branch-coverage suites."""

GST_RATE = {"food": 5, "electronics": 18, "clothing": 12}


def item_total(category, price, qty):
    """Apply the ten-item reduction before integer GST calculation."""
    if category not in GST_RATE:
        raise ValueError("unsupported category")
    if price < 0 or qty <= 0:
        raise ValueError("price and quantity are outside their allowed range")
    subtotal = price * qty
    if qty >= 10:
        subtotal = subtotal - subtotal // 10
    tax_amount = subtotal * GST_RATE[category] // 100
    return subtotal + tax_amount


def cart_discount(cart_value, is_prime, coupon):
    """Combine the cart tier, membership benefit and eligible coupon."""
    if cart_value >= 5000:
        saving = 500
    elif cart_value >= 2000:
        saving = 200
    else:
        saving = 0
    if is_prime:
        saving = saving + 100
    if coupon == "FLAT10" and cart_value >= 1000:
        saving = saving + cart_value // 10
    return saving


def shipping_fee(cart_value, is_prime, is_express):
    """Calculate ordinary delivery and the express surcharge."""
    if is_prime:
        delivery_charge = 0
    elif cart_value >= 500:
        delivery_charge = 0
    else:
        delivery_charge = 40
    if is_express:
        delivery_charge = delivery_charge + 100
        if is_prime:
            delivery_charge = delivery_charge - 50
    return delivery_charge
