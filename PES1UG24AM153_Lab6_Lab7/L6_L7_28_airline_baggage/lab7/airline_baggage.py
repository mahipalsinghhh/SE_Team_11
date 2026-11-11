import math


def parse_booking(code):
    """Parse 'AI-203-12A' -> ('AI', 203, 'A'). Returns None for invalid input."""
    if not isinstance(code, str):
        return None
    parts = code.strip().split('-')
    if len(parts) != 3:
        return None
    airline, flight, seat = (p.strip() for p in parts)
    # airline: 2-3 ASCII letters/digits
    if not (2 <= len(airline) <= 3 and airline.isascii() and airline.isalnum()):
        return None
    # flight: positive ASCII integer
    if not (flight.isascii() and flight.isdigit()) or int(flight) <= 0:
        return None
    # seat: row number followed by one letter, e.g. 12A
    if len(seat) < 2 or not seat.isascii():
        return None
    row, letter = seat[:-1], seat[-1]
    if not (row.isdigit() and int(row) > 0 and letter.isalpha()):
        return None
    return airline.upper(), int(flight), letter.upper()


def total_weight(weights_csv):
    """Sum comma-separated bag weights. Returns None for invalid input."""
    if not isinstance(weights_csv, str) or not weights_csv.strip():
        return None
    total = 0.0
    for w in weights_csv.split(','):
        w = w.strip()
        if not w:
            return None
        try:
            value = float(w)
        except ValueError:
            return None
        # reject nan, inf and negative weights
        if not math.isfinite(value) or value < 0:
            return None
        total += value
    if not math.isfinite(total):
        return None
    return total


def tag_label(name):
    """'rahul sharma' -> 'R. SHARMA'. Returns None for invalid input."""
    if not isinstance(name, str):
        return None
    parts = name.split()
    if len(parts) < 2:
        return None
    first, last = parts[0], parts[-1]
    if not first[0].isalpha():
        return None
    return first[0].upper() + '. ' + last.upper()


def main():
    print("==== Running parse_booking ====")
    user_input = input("Enter a booking code (e.g. AI-203-12A): ")
    result = parse_booking(user_input)
    if result is None:
        print("Invalid booking code. Expected format like AI-203-12A.")
    else:
        print("Airline, Flight and Seat Letter:", result)

    print("\n==== Running total_weight ====")
    user_input = input("Enter bag weights in kg as CSV (e.g. 12.5,7,23): ")
    result = total_weight(user_input)
    if result is None:
        print("Invalid weights. Enter non-negative numbers separated by commas.")
    else:
        print("Total Weight:", result)

    print("\n==== Running tag_label ====")
    user_input = input("Enter a passenger name (first and last): ")
    result = tag_label(user_input)
    if result is None:
        print("Invalid name. Enter a first and last name.")
    else:
        print("Tag Label:", result)


if __name__ == "__main__":
    main()
