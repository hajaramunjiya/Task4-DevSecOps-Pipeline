import pandas as pd

from src.interfaces import DataSource, Validator, Transformer, Analytics, ReportWriter


class TaxiDemandPipeline:
    """Coordinates ingestion, validation, transformation, analytics and output.

    Dependency Inversion Principle: every constructor parameter is typed
    against an abstraction in src/interfaces.py, not a concrete class.
    This class never imports ParquetDataSource, CsvDataSource,
    CsvJsonReportWriter or ParquetReportWriter directly - main.py/app.py
    is the only place those concrete choices are made (see
    build_pipeline() in app.py). That is what lets
    tests/test_pipeline.py exercise this class with fast, in-memory fakes
    instead of real files.
    """

    def __init__(
        self,
        source: DataSource,
        validator: Validator,
        transformer: Transformer,
        analytics: Analytics,
        writer: ReportWriter,
    ):
        self.source = source
        self.validator = validator
        self.transformer = transformer
        self.analytics = analytics
        self.writer = writer

    def run(self) -> dict:
        hourly_parts = []
        zone_parts = []

        for batch in self.source.batches():
            valid = self.validator.validate(batch)
            transformed = self.transformer.transform(valid)
            hourly_parts.append(self.analytics.hourly(transformed))
            zone_parts.append(self.analytics.by_zone(transformed))

        # Combine only the much smaller aggregated results, not the raw rows.
        hourly = (
            pd.concat(hourly_parts)
            .groupby("pickup_hour", as_index=False)["trip_count"]
            .sum()
            .sort_values("pickup_hour")
        )
        zones = (
            pd.concat(zone_parts)
            .groupby("PULocationID", as_index=False)
            .agg(
                trip_count=("trip_count", "sum"),
                total_distance=("total_distance", "sum"),
                total_fare=("total_fare", "sum"),
            )
            .sort_values("trip_count", ascending=False)
        )

        summary = self.analytics.summary(hourly, zones)
        self.writer.write(hourly, zones, summary)
        return summary
