import pandas as pd

from src.interfaces import Analytics


class DemandAnalytics(Analytics):
    """Calculates client-facing demand summaries."""

    def hourly(self, frame: pd.DataFrame) -> pd.DataFrame:
        return (
            frame.groupby("pickup_hour", as_index=False)
            .size()
            .rename(columns={"size": "trip_count"})
            .sort_values("pickup_hour")
        )

    def by_zone(self, frame: pd.DataFrame) -> pd.DataFrame:
        return (
            frame.groupby("PULocationID", as_index=False)
            .agg(
                trip_count=("PULocationID", "size"),
                total_distance=("trip_distance", "sum"),
                total_fare=("fare_amount", "sum"),
            )
            .sort_values("trip_count", ascending=False)
        )

    def summary(self, hourly: pd.DataFrame, zones: pd.DataFrame) -> dict:
        peak = hourly.loc[hourly["trip_count"].idxmax()]
        return {
            "total_trips_processed": int(hourly["trip_count"].sum()),
            "peak_hour": int(peak["pickup_hour"]),
            "peak_hour_trip_count": int(peak["trip_count"]),
            "top_pickup_zone": int(zones.iloc[0]["PULocationID"]) if not zones.empty else None,
        }
