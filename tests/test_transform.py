import pandas as pd

from src.transform import TripDataTransformer


def test_transform_derives_pickup_hour_and_date():
    frame = pd.DataFrame({
        "tpep_pickup_datetime": pd.to_datetime(["2026-01-01 14:30:00"]),
        "tpep_dropoff_datetime": pd.to_datetime(["2026-01-01 14:45:00"]),
        "PULocationID": [42],
        "trip_distance": [3.1],
        "fare_amount": [15.0],
    })
    result = TripDataTransformer().transform(frame)

    assert result.loc[0, "pickup_hour"] == 14
    assert list(result.columns) == [
        "pickup_hour", "pickup_date", "PULocationID", "trip_distance", "fare_amount",
    ]
