BERTHS = ["SU", "LB", "MB", "UB", "LB", "MB", "UB", "SL"]


def parse_pnr(pnr):
    if not isinstance(pnr, str):
        raise ValueError("PNR must be a string")
    pnr = pnr.strip()
    if len(pnr) != 10 or not pnr.isdigit():
        raise ValueError("PNR must be a 10-digit numeric string")
    return int(pnr[0]), int(pnr[1:])


def journey_distance(distances_csv):
    if not isinstance(distances_csv, str) or not distances_csv.strip():
        raise ValueError("distances_csv must be a non-empty string")
    parts = [p.strip() for p in distances_csv.split(",")]
    if len(parts) < 2 or any(not p for p in parts):
        raise ValueError("distances_csv must contain at least two distances")
    distances = [int(d) for d in parts]
    total = distances[-1] - distances[0]
    if total < 0:
        raise ValueError("destination distance cannot be less than origin")
    return total


def berth_type(seat):
    if not isinstance(seat, str) or "-" not in seat:
        raise ValueError("seat must be a string in '<coach>-<number>' format")
    parts = seat.split("-")
    if len(parts) != 2:
        raise ValueError("seat must contain exactly one '-'")
    coach, number_str = parts[0].strip(), parts[1].strip()
    if not coach:
        raise ValueError("coach cannot be empty")
    number = int(number_str)
    if number <= 0:
        raise ValueError("seat number must be positive")
    return coach.upper(), BERTHS[number % 8]


def main():
    print("==== Running parse_pnr ====")
    user_input = input("Enter a 10 digit PNR (e.g. 4521367890): ")
    result = parse_pnr(user_input)
    print("Zone and Number:", result)

    print("\n==== Running journey_distance ====")
    user_input = input("Enter station distances as CSV (e.g. 0,120,340): ")
    result = journey_distance(user_input)
    print("Total Distance:", result)

    print("\n==== Running berth_type ====")
    user_input = input("Enter coach and seat (e.g. S3-45): ")
    result = berth_type(user_input)
    print("Coach and Berth:", result)


if __name__ == "__main__":
    main()
