"""
Generates a schema-accurate sample dataset that mirrors the real NYC TLC
Yellow Taxi Trip Record schema (tpep_pickup_datetime, tpep_dropoff_datetime,
PULocationID, trip_distance, fare_amount, plus common companion columns).

Why this exists: the real monthly TLC files are hosted on nyc.gov/AWS and
are several hundred MB to a few GB each - too large to bundle in a
coursework submission, and not reachable from this build environment's
network allowlist. This script produces a smaller but schema-identical
stand-in (including a small proportion of deliberately invalid rows -
negative fares, negative distances, bad dates - so the validator has
real work to do) purely so the application can actually be run and
produce real, verifiable evidence for this submission, rather than only
being described.

To use the REAL dataset instead: download any monthly file from
https://home4.nyc.gov/site/tlc/about/tlc-trip-record-data.page and run:
    python3 app.py --input yellow_tripdata_2025-01.parquet --output output
No code changes are required - ParquetDataSource reads the real schema directly.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_ROWS = 1_000_000


def generate() -> pd.DataFrame:
    pickup = pd.to_datetime("2026-01-01") + pd.to_timedelta(
        RNG.integers(0, 60 * 60 * 24 * 31, N_ROWS), unit="s"
    )
    trip_minutes = RNG.exponential(12, N_ROWS).clip(1, 180)
    dropoff = pickup + pd.to_timedelta(trip_minutes, unit="m")

    frame = pd.DataFrame({
        "tpep_pickup_datetime": pickup,
        "tpep_dropoff_datetime": dropoff,
        "PULocationID": RNG.integers(1, 265, N_ROWS),
        "DOLocationID": RNG.integers(1, 265, N_ROWS),
        "trip_distance": RNG.exponential(2.3, N_ROWS).round(2),
        "fare_amount": RNG.exponential(14, N_ROWS).round(2),
        "passenger_count": RNG.integers(1, 5, N_ROWS),
        "payment_type": RNG.integers(1, 3, N_ROWS),
    })

    # Inject a realistic proportion of data-quality problems, mirroring
    # TLC's own disclaimer that it does not guarantee data accuracy.
    n_bad = int(N_ROWS * 0.015)
    bad_idx = RNG.choice(N_ROWS, n_bad, replace=False)
    frame.loc[bad_idx[: n_bad // 3], "trip_distance"] = -1.0
    frame.loc[bad_idx[n_bad // 3: 2 * n_bad // 3], "fare_amount"] = -5.0
    frame.loc[bad_idx[2 * n_bad // 3:], "tpep_pickup_datetime"] = pd.NaT

    return frame


if __name__ == "__main__":
    df = generate()
    df.to_parquet("data/sample_trip_data.parquet", index=False)
    df.to_csv("data/sample_trip_data.csv", index=False)
    print(f"Generated {len(df):,} rows -> data/sample_trip_data.parquet / .csv")
