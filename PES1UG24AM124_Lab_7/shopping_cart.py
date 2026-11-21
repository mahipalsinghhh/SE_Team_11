"""Validated parsers for the shopping-cart fuzz-testing exercise."""
import re

ZONES = {"1": "North", "2": "North", "3": "West", "4": "West",
         "5": "South", "6": "South", "7": "East", "8": "East"}
ENTRY_PATTERN = re.compile(r"([^:,\r\n]+):([0-9]+)x([0-9]+)")
OFFER_PATTERN = re.compile(r"OFF([0-9]{1,3})")
POSTAL_PATTERN = re.compile(r"[0-9]{6}")


def cart_total(cart):
    """Add non-negative integer price/quantity pairs in a CSV cart."""
    if not isinstance(cart, str) or not cart.strip():
        raise ValueError("a cart must contain at least one item")
    running_total = 0
    for entry in cart.split(","):
        parsed = ENTRY_PATTERN.fullmatch(entry.strip())
        if parsed is None or not parsed[1].strip():
            raise ValueError("each entry must use name:pricexqty")
        unit_cost, units = int(parsed[2]), int(parsed[3])
        running_total += unit_cost * units
    return running_total


def promo_percent(code):
    """Accept OFF0 through OFF100, ignoring case and outer whitespace."""
    if not isinstance(code, str):
        raise ValueError("an offer must be text")
    offer = OFFER_PATTERN.fullmatch(code.strip().upper())
    if offer is None:
        raise ValueError("use OFF followed by one to three ASCII digits")
    reduction = int(offer[1])
    if not 0 <= reduction <= 100:
        raise ValueError("the offer percentage must be between 0 and 100")
    return reduction


def delivery_zone(pincode):
    """Map supported six-digit ASCII pincodes to a delivery region."""
    if not isinstance(pincode, str):
        raise ValueError("a pincode must be text")
    postal_text = pincode.strip()
    if POSTAL_PATTERN.fullmatch(postal_text) is None:
        raise ValueError("a pincode needs exactly six ASCII digits")
    zone = ZONES.get(postal_text[0])
    if zone is None:
        raise ValueError("the pincode prefix has no configured zone")
    return zone


def main():
    """Show each parser without exposing an unhandled input error."""
    tasks = [("Cart (name:pricexqty): ", cart_total),
             ("Offer (OFF20): ", promo_percent),
             ("Pincode: ", delivery_zone)]
    for prompt, parser in tasks:
        try:
            print(parser(input(prompt)))
        except ValueError as error:
            print("Input rejected:", error)
        except EOFError:
            print("Input ended.")
            break


if __name__ == "__main__":
    main()
