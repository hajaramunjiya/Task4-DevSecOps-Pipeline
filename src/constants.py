"""Named constants shared across the pipeline.

Previously REQUIRED_COLUMNS was defined twice (once in ParquetDataSource,
once inline in TripDataValidator.validate) - a DRY violation, since the
two copies could silently drift apart. It now lives in exactly one place.
"""

REQUIRED_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "trip_distance",
    "fare_amount",
}

DEFAULT_BATCH_SIZE = 100_000
