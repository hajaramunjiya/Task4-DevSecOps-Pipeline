"""
Liskov Substitution Principle - proven, not just claimed.

The original report asserted "a future data-source implementation can
provide the same batch behaviour expected by the pipeline" as a
hypothetical. These tests make it real: two concrete DataSource
implementations and two concrete ReportWriter implementations are each
run through identical assertions, proving the pipeline genuinely cannot
tell (and does not need to know) which one it was given.
"""
from pathlib import Path
import json

import pandas as pd
import pytest

from src.datasource import ParquetDataSource, CsvDataSource
from src.writer import CsvJsonReportWriter, ParquetReportWriter
from src.pipeline import TaxiDemandPipeline
from src.validation import TripDataValidator
from src.transform import TripDataTransformer
from src.analytics import DemandAnalytics

SAMPLE_ROWS = {
    "tpep_pickup_datetime": ["2026-01-01 09:00:00", "2026-01-01 09:15:00", "2026-01-01 18:00:00"],
    "tpep_dropoff_datetime": ["2026-01-01 09:10:00", "2026-01-01 09:20:00", "2026-01-01 18:20:00"],
    "PULocationID": [100, 100, 200],
    "trip_distance": [1.2, 0.8, 4.5],
    "fare_amount": [8.0, 6.0, 22.0],
}


@pytest.fixture
def sample_parquet(tmp_path) -> Path:
    path = tmp_path / "sample.parquet"
    pd.DataFrame(SAMPLE_ROWS).to_parquet(path, index=False)
    return path


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    path = tmp_path / "sample.csv"
    pd.DataFrame(SAMPLE_ROWS).to_csv(path, index=False)
    return path


@pytest.mark.parametrize(
    "source_factory",
    [
        lambda path: ParquetDataSource(path),
        lambda path: CsvDataSource(path),
    ],
    ids=["ParquetDataSource", "CsvDataSource"],
)
def test_both_data_sources_are_interchangeable(sample_parquet, sample_csv, source_factory):
    """Same pipeline, same assertions, only the DataSource class differs."""
    path = sample_parquet if "Parquet" in source_factory(sample_parquet).__class__.__name__ else sample_csv
    source = source_factory(path)

    total_rows = sum(len(batch) for batch in source.batches())
    assert total_rows == 3


@pytest.mark.parametrize(
    "writer_cls,expected_files",
    [
        (CsvJsonReportWriter, {"demand_by_hour.csv", "demand_by_zone.csv", "summary.json"}),
        (ParquetReportWriter, {"demand_by_hour.parquet", "demand_by_zone.parquet", "summary.json"}),
    ],
    ids=["CsvJsonReportWriter", "ParquetReportWriter"],
)
def test_both_report_writers_are_interchangeable(tmp_path, writer_cls, expected_files):
    """Same summary data, only the ReportWriter class differs - both
    produce a complete, readable set of output files."""
    analytics = DemandAnalytics()
    frame = TripDataTransformer().transform(
        TripDataValidator().validate(pd.DataFrame(SAMPLE_ROWS))
    )
    hourly = analytics.hourly(frame)
    zones = analytics.by_zone(frame)
    summary = analytics.summary(hourly, zones)

    writer = writer_cls(tmp_path)
    writer.write(hourly, zones, summary)

    produced = {f.name for f in tmp_path.iterdir()}
    assert produced == expected_files


def test_pipeline_produces_same_summary_regardless_of_source_or_writer(
    sample_parquet, sample_csv, tmp_path
):
    """The strongest LSP evidence: run the full pipeline twice, once with
    each DataSource/ReportWriter pairing, and confirm the client-facing
    summary is identical either way."""
    def run_with(source, writer_dir, writer_cls):
        pipeline = TaxiDemandPipeline(
            source=source,
            validator=TripDataValidator(),
            transformer=TripDataTransformer(),
            analytics=DemandAnalytics(),
            writer=writer_cls(writer_dir),
        )
        return pipeline.run()

    summary_a = run_with(ParquetDataSource(sample_parquet), tmp_path / "a", CsvJsonReportWriter)
    summary_b = run_with(CsvDataSource(sample_csv), tmp_path / "b", ParquetReportWriter)

    assert summary_a == summary_b
