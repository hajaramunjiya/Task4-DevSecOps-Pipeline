import pandas as pd
import pytest

from src.validation import TripDataValidator
from src.exceptions import SchemaError


def make_frame(**overrides) -> pd.DataFrame:
    base = {
        "tpep_pickup_datetime": ["2026-01-01 10:00:00", "2026-01-01 11:00:00"],
        "tpep_dropoff_datetime": ["2026-01-01 10:10:00", "2026-01-01 11:10:00"],
        "PULocationID": [1, 2],
        "trip_distance": [2.5, 1.2],
        "fare_amount": [10, 12],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_schema_error_raised_when_column_missing():
    frame = make_frame().drop(columns=["fare_amount"])
    with pytest.raises(SchemaError):
        TripDataValidator().validate(frame)


def test_invalid_dates_are_removed():
    frame = make_frame(tpep_pickup_datetime=["2026-01-01 10:00:00", "not-a-date"])
    result = TripDataValidator().validate(frame)
    assert len(result) == 1


def test_invalid_negative_distance_is_removed():
    frame = make_frame(trip_distance=[2.5, -1])
    result = TripDataValidator().validate(frame)
    assert len(result) == 1


def test_invalid_negative_fare_is_removed():
    frame = make_frame(fare_amount=[10, -5])
    result = TripDataValidator().validate(frame)
    assert len(result) == 1


def test_valid_rows_pass_through_unchanged_in_count():
    result = TripDataValidator().validate(make_frame())
    assert len(result) == 2
