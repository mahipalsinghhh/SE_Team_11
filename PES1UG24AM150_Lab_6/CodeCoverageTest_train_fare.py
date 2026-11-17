import pytest
from train_fare import base_fare, concession, tatkal_charge


def test_base_fare_valid_classes():
    assert base_fare("SL", 500) == 500
    assert base_fare("3A", 100) == 200
    assert base_fare("2A", 100) == 300
    assert base_fare("1A", 100) == 500


def test_base_fare_minimum_and_errors():
    assert base_fare("SL", 10) == 50
    with pytest.raises(ValueError, match="unknown class"):
        base_fare("EC", 100)
    with pytest.raises(ValueError, match="invalid distance"):
        base_fare("SL", 0)


def test_concession_all_categories():
    assert concession(30, "M", True) == 0
    assert concession(3, "F", False) == 100
    assert concession(10, "M", False) == 50
    assert concession(65, "F", False) == 50
    assert concession(65, "M", False) == 40
    assert concession(30, "M", False) == 0


def test_tatkal_charge_all_paths():
    assert tatkal_charge("SL", 2000) == 200
    assert tatkal_charge("3A", 2000) == 400
    assert tatkal_charge("SL", 500) == 100
