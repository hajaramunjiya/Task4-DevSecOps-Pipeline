from pathlib import Path
import argparse
import json

from src.pipeline import TaxiDemandPipeline
from src.datasource import ParquetDataSource, CsvDataSource
from src.validation import TripDataValidator
from src.transform import TripDataTransformer
from src.analytics import DemandAnalytics
from src.writer import CsvJsonReportWriter, ParquetReportWriter


def build_pipeline(input_path: str, output_dir: str, output_format: str = "csv") -> TaxiDemandPipeline:
    """Wires concrete implementations together. This is the ONLY function
    in the application that imports concrete DataSource/ReportWriter
    classes - everywhere else talks to the DataSource/ReportWriter
    abstractions in src/interfaces.py."""
    path = Path(input_path)
    source = CsvDataSource(path) if path.suffix.lower() == ".csv" else ParquetDataSource(path)

    writer = (
        ParquetReportWriter(Path(output_dir))
        if output_format == "parquet"
        else CsvJsonReportWriter(Path(output_dir))
    )

    return TaxiDemandPipeline(
        source=source,
        validator=TripDataValidator(),
        transformer=TripDataTransformer(),
        analytics=DemandAnalytics(),
        writer=writer,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="NYC taxi demand analytics")
    parser.add_argument("--input", required=True, help="Input TLC Parquet or CSV file")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument(
        "--output-format", choices=["csv", "parquet"], default="csv",
        help="Report output format (demonstrates OCP: swap writer with no pipeline changes)",
    )
    args = parser.parse_args()

    pipeline = build_pipeline(args.input, args.output, args.output_format)
    summary = pipeline.run()

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
