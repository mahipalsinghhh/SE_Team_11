FREE_ALLOWANCE = {"economy": 15, "premium": 25, "business": 40}


def baggage_fee(cabin, weight_kg, route, is_member):
    if cabin not in FREE_ALLOWANCE:
        raise ValueError("unknown cabin")
    if weight_kg < 0:
        raise ValueError("invalid weight")
    allowance = FREE_ALLOWANCE[cabin]
    if is_member and cabin != "business":
        allowance += 10
    excess = weight_kg - allowance
    if excess <= 0:
        return 0
    if route == "domestic":
        rate = 20
    else:
        rate = 45
    if excess > 20:
        rate = rate * 2
        if route == "international":
            rate += 10
    return excess * rate


def carry_on_ok(weight_kg, items, is_infant):
    if is_infant:
        return items <= 2
    if weight_kg > 7:
        return False
    return items <= 1


def check_in_status(minutes_before, has_baggage, is_international):
    if has_baggage:
        cutoff = 60
    else:
        cutoff = 45
    if is_international:
        cutoff += 60
    if minutes_before >= cutoff:
        return "open"
    elif minutes_before >= cutoff - 15:
        return "late"
    return "closed"
