import pandas as pd

from src.analytics import DemandAnalytics


def make_transformed_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "pickup_hour": [9, 9, 10, 10, 10],
        "pickup_date": ["2026-01-01"] * 5,
        "PULocationID": [100, 100, 200, 200, 200],
        "trip_distance": [1.0, 2.0, 1.5, 1.0, 0.5],
        "fare_amount": [10.0, 12.0, 8.0, 7.0, 6.0],
    })


def test_hourly_counts_match_controlled_sample():
    result = DemandAnalytics().hourly(make_transformed_frame())
    counts = dict(zip(result["pickup_hour"], result["trip_count"]))
    assert counts == {9: 2, 10: 3}


def test_by_zone_totals_match_controlled_sample():
    result = DemandAnalytics().by_zone(make_transformed_frame())
    zone_200 = result[result["PULocationID"] == 200].iloc[0]
    assert zone_200["trip_count"] == 3
    assert zone_200["total_distance"] == 3.0
    assert zone_200["total_fare"] == 21.0


def test_summary_identifies_peak_hour_and_top_zone():
    analytics = DemandAnalytics()
    frame = make_transformed_frame()
    hourly = analytics.hourly(frame)
    zones = analytics.by_zone(frame)
    summary = analytics.summary(hourly, zones)

    assert summary["total_trips_processed"] == 5
    assert summary["peak_hour"] == 10
    assert summary["top_pickup_zone"] == 200
