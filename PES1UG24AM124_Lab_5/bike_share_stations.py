"""SQLite bike-station operations for the static-analysis exercise."""

import secrets
import sqlite3

DATABASE = sqlite3.connect(":memory:")
DATABASE.execute(
    "CREATE TABLE stations (id INTEGER PRIMARY KEY, name TEXT, "
    "capacity INTEGER, bikes INTEGER)"
)


def add_station(name, capacity, bikes, log=None):
    """Store a station, returning the caller's log or a fresh log."""
    station_log = [] if log is None else log
    DATABASE.execute(
        "INSERT INTO stations (name, capacity, bikes) VALUES (?, ?, ?)",
        (name, capacity, bikes),
    )
    station_log.append(name)
    return station_log


def rent_bike(station_id):
    """Use an atomic conditional update to rent an available bike."""
    cursor = DATABASE.execute(
        "UPDATE stations SET bikes = bikes - 1 "
        "WHERE id = ? AND bikes > 0", (station_id,)
    )
    return cursor.rowcount == 1


def unlock_pin():
    """Generate a four-digit PIN using a security-oriented source."""
    return 1000 + secrets.randbelow(9000)


def full_stations():
    """List stations with no unused docking capacity."""
    records = DATABASE.execute(
        "SELECT name FROM stations WHERE bikes = capacity"
    )
    return [name for (name,) in records]


def reset_station(station_id):
    """Empty a station; leave database errors visible to the caller."""
    DATABASE.execute(
        "UPDATE stations SET bikes = 0 WHERE id = ?", (station_id,)
    )


def has_bikes(station_id):
    """Treat a missing station as unavailable instead of indexing None."""
    record = DATABASE.execute(
        "SELECT bikes FROM stations WHERE id = ?", (station_id,)
    ).fetchone()
    return record is not None and record[0] > 0


def main():
    """Show successful and unsuccessful station operations."""
    add_station("Library Gate", 6, 6)
    add_station("Sports Block", 9, 1)
    print("Rental outcomes:", rent_bike(2), rent_bike(99))
    print("Unlock PIN:", unlock_pin())
    print("Full stations:", full_stations())
    reset_station(1)
    print("Library bikes available:", has_bikes(1))


if __name__ == "__main__":
    main()
