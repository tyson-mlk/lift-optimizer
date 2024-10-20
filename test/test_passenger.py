import pytest

from base import Passenger

def test_calculate_direction():
    source_floor = 'A'
    target_floor = 'Z'
    test_case = Passenger.Passenger(source_floor, target_floor)
    expected_dir = 'U'

    assert test_case.dir == expected_dir

def test_source_target_diff():
    with pytest.raises(Exception):
        source_floor = 'A'
        target_floor = 'A'
        test_case = Passenger.Passenger(source_floor, target_floor)
