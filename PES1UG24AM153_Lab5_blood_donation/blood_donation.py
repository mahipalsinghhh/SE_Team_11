"""Blood bank donor registry: register donors, record donations, track stock.
"""
import os
import subprocess  # nosec B404 - used safely without a shell
import tempfile
from datetime import date, timedelta

OFFICER_PASSWORD = os.environ.get("OFFICER_PASSWORD", "")
donors = []
stock = {
    "A+": 0, "A-": 0, "B+": 0, "B-": 0,
    "O+": 0, "O-": 0, "AB+": 0, "AB-": 0,
}
COMPATIBLE = {
    "A+": ["A+", "A-", "O+", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"],
    "AB+": list(stock),
}


def register_donor(donor_name, blood_group, age, last_donation=None,
                   notes=None):
    """Register a donor if their blood group and age are valid."""
    if notes is None:
        notes = []
    if blood_group not in stock:
        raise ValueError("Unknown blood group")
    if age < 18 or age > 65:
        notes.append(donor_name + " is not eligible because of age")
        return False
    donors.append({"name": donor_name, "group": blood_group,
                   "last": last_donation})
    return True


def can_donate(donor):
    """Return True if at least 90 days have passed since the last donation."""
    if donor["last"] is None:
        return True
    return date.today() - donor["last"] >= timedelta(days=90)


def record_donation(donor_name, units=1):
    """Add units to stock for an eligible donor."""
    for donor in donors:
        if donor["name"] == donor_name and can_donate(donor):
            stock[donor["group"]] += units
            donor["last"] = date.today()
            return True
    return False


def units_for(patient_group):
    """Return total compatible units available for a patient's group."""
    try:
        return sum(stock[group] for group in COMPATIBLE[patient_group])
    except KeyError:
        return 0


def is_universal(blood_group):
    """Return True for the universal donor (O-) or recipient (AB+) group."""
    return blood_group in ("O-", "AB+")


def low_stock(threshold=2):
    """Return the blood groups whose stock is below the threshold."""
    return [group for group, units in stock.items() if units < threshold]


def donor_sheet_path():
    """Create a temporary CSV file safely and return its path."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    return path


def notify_donors(phone_list):
    """Send an SMS to each phone number without using a shell."""
    subprocess.run(["send-sms", *phone_list], check=False)  # nosec B603 B607


def main():
    """Run a small demo of the donor registry."""
    register_donor("Arjun", "O+", 25)
    register_donor("Priya", "A+", 30, date.today() - timedelta(days=30))
    register_donor("Old Donor", "B+", 70)
    register_donor("Farah", "O-", 41)
    record_donation("Arjun", 2)
    record_donation("Priya")
    record_donation("Farah")
    print("Stock:", stock)
    print("Units for an A+ patient:", units_for("A+"))
    print("Units for a Z+ patient:", units_for("Z+"))
    print("Is O- universal?", is_universal("O-"))
    print("Low stock groups:", low_stock())  # below 2 units
    eligible = [donor["name"] for donor in donors if can_donate(donor)]
    print("Donors eligible today:", eligible)


if __name__ == "__main__":
    main()
