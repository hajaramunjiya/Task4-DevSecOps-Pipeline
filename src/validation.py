import pandas as pd

from src.interfaces import Validator
from src.constants import REQUIRED_COLUMNS
from src.exceptions import SchemaError


class TripDataValidator(Validator):
    """Validates the minimum fields and values needed by the analytics layer."""

    def validate(self, frame: pd.DataFrame) -> pd.DataFrame:
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise SchemaError(f"Missing required columns: {sorted(missing)}")

        frame = frame.copy()
        frame["tpep_pickup_datetime"] = pd.to_datetime(
            frame["tpep_pickup_datetime"], errors="coerce"
        )
        frame["tpep_dropoff_datetime"] = pd.to_datetime(
            frame["tpep_dropoff_datetime"], errors="coerce"
        )
        frame = frame.dropna(subset=["tpep_pickup_datetime", "PULocationID"])
        frame = frame[frame["trip_distance"].fillna(0) >= 0]
        frame = frame[frame["fare_amount"].fillna(0) >= 0]
        return frame
