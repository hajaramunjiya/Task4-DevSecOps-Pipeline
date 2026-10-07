import pandas as pd

from src.interfaces import Transformer


class TripDataTransformer(Transformer):
    """Converts raw trip records into analysis-ready records."""

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        result["pickup_hour"] = result["tpep_pickup_datetime"].dt.hour
        result["pickup_date"] = result["tpep_pickup_datetime"].dt.date
        result["PULocationID"] = result["PULocationID"].astype("Int64")
        return result[[
            "pickup_hour",
            "pickup_date",
            "PULocationID",
            "trip_distance",
            "fare_amount",
        ]]
