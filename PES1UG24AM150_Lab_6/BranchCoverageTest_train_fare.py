import pytest
from train_fare import base_fare, concession, tatkal_charge


def test_base_fare_branches():
    # Invalid class branch
    with pytest.raises(ValueError, match="unknown class"):
        base_fare("INVALID", 100)
    # Invalid distance branches (<= 0)
    with pytest.raises(ValueError, match="invalid distance"):
        base_fare("SL", 0)
    with pytest.raises(ValueError, match="invalid distance"):
        base_fare("SL", -25)
    # Minimum fare branch (fare < 50)
    assert base_fare("SL", 20) == 50
    # Regular fare branch (fare >= 50)
    assert base_fare("2A", 50) == 150


def test_concession_branches():
    # Tatkal True vs False
    assert concession(4, "F", True) == 0
    # Age < 5
    assert concession(4, "M", False) == 100
    # Age <= 12 (boundary 5 and 12)
    assert concession(5, "F", False) == 50
    assert concession(12, "M", False) == 50
    # Age >= 60 with gender == "F" vs != "F"
    assert concession(60, "F", False) == 50
    assert concession(60, "M", False) == 40
    # Default adult (12 < age < 60)
    assert concession(13, "F", False) == 0
    assert concession(59, "M", False) == 0


def test_tatkal_charge_branches():
    # SL class, charge within [100, 400]
    assert tatkal_charge("SL", 1500) == 150
    # Non-SL class, charge > 400 (clamped to 400)
    assert tatkal_charge("1A", 2000) == 400
    # SL class, charge < 100 (clamped to 100)
    assert tatkal_charge("SL", 400) == 100
    # Non-SL class, charge within [100, 400]
    assert tatkal_charge("3A", 1000) == 300
