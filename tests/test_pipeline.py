"""Demonstrates the practical payoff of Dependency Inversion: because
TaxiDemandPipeline depends only on the abstractions in interfaces.py, it
can be tested end-to-end with tiny in-memory fakes - no real file, no
real Parquet/CSV I/O, runs in milliseconds."""
from typing import Dict, Iterator
import pandas as pd

from src.interfaces import DataSource, ReportWriter
from src.pipeline import TaxiDemandPipeline
from src.validation import TripDataValidator
from src.transform import TripDataTransformer
from src.analytics import DemandAnalytics


class FakeDataSource(DataSource):
    def batches(self) -> Iterator[pd.DataFrame]:
        yield pd.DataFrame({
            "tpep_pickup_datetime": ["2026-01-01 08:00:00", "2026-01-01 08:30:00"],
            "tpep_dropoff_datetime": ["2026-01-01 08:10:00", "2026-01-01 08:40:00"],
            "PULocationID": [1, 1],
            "trip_distance": [2.0, 3.0],
            "fare_amount": [9.0, 11.0],
        })
        yield pd.DataFrame({
            "tpep_pickup_datetime": ["2026-01-01 08:15:00"],
            "tpep_dropoff_datetime": ["2026-01-01 08:25:00"],
            "PULocationID": [2],
            "trip_distance": [1.0],
            "fare_amount": [5.0],
        })


class CapturingWriter(ReportWriter):
    def __init__(self):
        self.captured = None

    def write(self, hourly: pd.DataFrame, zones: pd.DataFrame, summary: Dict) -> None:
        self.captured = summary


def test_pipeline_runs_end_to_end_with_fakes_across_multiple_batches():
    writer = CapturingWriter()
    pipeline = TaxiDemandPipeline(
        source=FakeDataSource(),
        validator=TripDataValidator(),
        transformer=TripDataTransformer(),
        analytics=DemandAnalytics(),
        writer=writer,
    )

    summary = pipeline.run()

    assert summary["total_trips_processed"] == 3
    assert summary["peak_hour"] == 8
    assert summary["top_pickup_zone"] == 1
    assert writer.captured == summary
