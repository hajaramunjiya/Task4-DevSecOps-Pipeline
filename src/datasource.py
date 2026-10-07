from pathlib import Path
from typing import Iterator
import pandas as pd

from src.interfaces import DataSource
from src.constants import DEFAULT_BATCH_SIZE
from src.exceptions import EmptySourceError


class ParquetDataSource(DataSource):
    """Streams batches from a Parquet file without loading the whole file
    into memory - the format TLC actually publishes current trip data in."""

    def __init__(self, path: Path, batch_size: int = DEFAULT_BATCH_SIZE):
        self.path = Path(path)
        self.batch_size = batch_size

    def batches(self) -> Iterator[pd.DataFrame]:
        import pyarrow.parquet as pq

        if not self.path.exists():
            raise EmptySourceError(f"Parquet file not found: {self.path}")

        parquet = pq.ParquetFile(self.path)
        yielded = False
        for batch in parquet.iter_batches(batch_size=self.batch_size):
            yielded = True
            yield batch.to_pandas()

        if not yielded:
            raise EmptySourceError(f"Parquet file '{self.path}' contained no batches.")


class CsvDataSource(DataSource):
    """Streams batches from a CSV file using pandas' chunked reader.

    This exists to prove the Liskov Substitution claim rather than just
    assert it: TaxiDemandPipeline (see pipeline.py) accepts any DataSource,
    so this class can be swapped in for ParquetDataSource with zero changes
    to the pipeline, the validator, the analytics or the writer. Useful
    when a client hands over a CSV export instead of the native Parquet
    TLC format - exactly the kind of extension OCP is meant to make cheap.
    """

    def __init__(self, path: Path, batch_size: int = DEFAULT_BATCH_SIZE):
        self.path = Path(path)
        self.batch_size = batch_size

    def batches(self) -> Iterator[pd.DataFrame]:
        if not self.path.exists():
            raise EmptySourceError(f"CSV file not found: {self.path}")

        yielded = False
        for chunk in pd.read_csv(self.path, chunksize=self.batch_size):
            yielded = True
            yield chunk

        if not yielded:
            raise EmptySourceError(f"CSV file '{self.path}' contained no rows.")
