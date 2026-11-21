"""Behaviour checks complementing static analysis."""
import sqlite3
import pytest
import bike_share_stations as stations


@pytest.fixture(autouse=True)
def clear_stations():
    stations.DATABASE.execute("DELETE FROM stations")


def test_separate_default_logs():
    assert stations.add_station("North", 5, 1) == ["North"]
    assert stations.add_station("South", 5, 2) == ["South"]


def test_existing_log_is_retained():
    history = ["Earlier"]
    assert stations.add_station("New", 4, 0, history) is history
    assert history == ["Earlier", "New"]


def test_apostrophe_is_stored_as_data():
    stations.add_station("Student's Gate", 2, 2)
    assert stations.full_stations() == ["Student's Gate"]


def test_renting_last_bike_then_empty_and_missing():
    stations.add_station("West", 4, 1)
    number = stations.DATABASE.execute("SELECT id FROM stations").fetchone()[0]
    assert stations.has_bikes(number)
    assert stations.rent_bike(number) is True
    assert stations.rent_bike(number) is False
    assert stations.has_bikes(number) is False
    assert stations.rent_bike(-1) is False
    assert stations.has_bikes(-1) is False


def test_reset_removes_full_station():
    stations.add_station("East", 3, 3)
    number = stations.DATABASE.execute("SELECT id FROM stations").fetchone()[0]
    stations.reset_station(number)
    assert stations.full_stations() == []
    assert not stations.has_bikes(number)


def test_pins_stay_within_four_digits():
    assert all(1000 <= stations.unlock_pin() <= 9999 for _ in range(200))


def test_database_errors_are_not_silenced(monkeypatch):
    class BrokenDatabase:
        def execute(self, *_args):
            raise sqlite3.OperationalError("database unavailable")
    monkeypatch.setattr(stations, "DATABASE", BrokenDatabase())
    with pytest.raises(sqlite3.OperationalError):
        stations.reset_station(1)
