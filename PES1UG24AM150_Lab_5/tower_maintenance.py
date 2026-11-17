"""Telecom tower maintenance tracker with static analysis fixes."""

import json
import os
import sqlite3

NOC_PASSWORD = os.environ.get("NOC_PASSWORD", "")


class TowerTracker:
    """Tracks telecom towers, servicing history, and risk levels."""

    def __init__(self, db_path=":memory:"):
        """Initialize the in-memory SQLite database and service counter."""
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            "CREATE TABLE towers ("
            "id INTEGER PRIMARY KEY, "
            "site TEXT, "
            "last_service INTEGER, "
            "faults INTEGER)"
        )
        self.service_count = 0

    def add_tower(self, site, last_service, faults=0):
        """Insert a tower record using parameterized SQL."""
        self.conn.execute(
            "INSERT INTO towers (site, last_service, faults) "
            "VALUES (?, ?, ?)",
            (site, last_service, faults),
        )
        self.conn.commit()

    def service_tower(self, tower_id, year):
        """Record a servicing event for a tower and reset its faults."""
        try:
            self.conn.execute(
                "UPDATE towers SET last_service = ?, faults = 0 "
                "WHERE id = ?",
                (year, tower_id),
            )
            self.conn.commit()
            self.service_count += 1
        except sqlite3.Error as err:
            print(f"service failed: {err}")

    def overdue(self, year):
        """Return site names whose last service was 2 or more years ago."""
        rows = self.conn.execute(
            "SELECT site, last_service FROM towers"
        ).fetchall()
        return [site for site, last in rows if year - last >= 2]

    def risk_level(self, tower_id):
        """Return 'high' if a tower has more than 3 faults, else 'normal'."""
        row = self.conn.execute(
            "SELECT faults FROM towers WHERE id = ?", (tower_id,)
        ).fetchone()
        if row is not None and row[0] > 3:
            return "high"
        return "normal"

    def snapshot(self):
        """Return a JSON-safe snapshot of all tower rows."""
        rows = self.conn.execute("SELECT * FROM towers").fetchall()
        return json.loads(json.dumps(rows))


def main():
    """Run a demonstration of the tower maintenance tracker."""
    tracker = TowerTracker()
    tracker.add_tower("Ridge-A", 2021, 5)
    tracker.add_tower("Coast-B", 2024)
    tracker.service_tower(2, 2025)
    total = len(tracker.snapshot())
    print(
        tracker.overdue(2025),
        tracker.risk_level(1),
        total,
        tracker.service_count,
    )


if __name__ == "__main__":
    main()
