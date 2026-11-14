GST_RATE = {"food": 5, "electronics": 18, "clothing": 12}


def item_total(category, price, qty):
    if category not in GST_RATE:
        raise ValueError("unknown category")
    if price < 0 or qty <= 0:
        raise ValueError("invalid price or quantity")
    amount = price * qty
    if qty >= 10:
        amount -= amount // 10
    return amount + amount * GST_RATE[category] // 100


def cart_discount(cart_value, is_prime, coupon):
    if cart_value >= 5000:
        discount = 500
    elif cart_value >= 2000:
        discount = 200
    else:
        discount = 0
    if is_prime:
        discount += 100
    if coupon == "FLAT10" and cart_value >= 1000:
        discount += cart_value // 10
    return discount


def shipping_fee(cart_value, is_prime, is_express):
    if is_prime:
        fee = 0
    elif cart_value >= 500:
        fee = 0
    else:
        fee = 40
    if is_express:
        fee += 100
        if is_prime:
            fee -= 50
    return fee
