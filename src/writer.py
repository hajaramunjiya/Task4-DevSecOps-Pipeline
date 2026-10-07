from pathlib import Path
import json
import pandas as pd

from src.interfaces import ReportWriter


class CsvJsonReportWriter(ReportWriter):
    """Writes outputs as CSV (for spreadsheet review) and JSON (for
    downstream systems) - the original output format."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, hourly: pd.DataFrame, zones: pd.DataFrame, summary: dict) -> None:
        hourly.to_csv(self.output_dir / "demand_by_hour.csv", index=False)
        zones.to_csv(self.output_dir / "demand_by_zone.csv", index=False)
        with open(self.output_dir / "summary.json", "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)


class ParquetReportWriter(ReportWriter):
    """Writes outputs as Parquet instead of CSV/JSON.

    Added purely to extend the system (Open/Closed Principle): a client
    who wants to feed results straight into another Parquet-based
    pipeline can now request this writer instead. Nothing in
    TaxiDemandPipeline, DemandAnalytics or the validator had to change to
    support it - only a new class was written, and it is proven
    interchangeable with CsvJsonReportWriter by
    tests/test_liskov_substitution.py.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, hourly: pd.DataFrame, zones: pd.DataFrame, summary: dict) -> None:
        hourly.to_parquet(self.output_dir / "demand_by_hour.parquet", index=False)
        zones.to_parquet(self.output_dir / "demand_by_zone.parquet", index=False)
        with open(self.output_dir / "summary.json", "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)
