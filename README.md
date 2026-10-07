# NYC Taxi Demand Analytics - Task 3

A large-dataset OOP application built for ModernDayTech's Task 3 exercise
(Unit 9), modelled on the schema of the NYC TLC Trip Record Data
(https://home4.nyc.gov/site/tlc/about/tlc-trip-record-data.page), a real,
non-commercial, multi-gigabyte-scale public dataset comparable to those
listed at datasetlist.com.

## Client requirement
A city transport operations team wants to convert large volumes of raw
taxi trip records into reliable, client-facing demand summaries (by hour
and by pickup zone) without needing to inspect every raw row.

## What changed in this revision
The original prototype described SOLID principles in its report but the
code contained no actual abstractions to depend on, no second
implementation to prove substitutability, and no evidence the application
had ever been run. This revision fixes all three:

1. **Real interfaces** (`src/interfaces.py`): `DataSource`, `Validator`,
   `Transformer`, `Analytics`, `ReportWriter` are now formal `ABC`
   classes. `TaxiDemandPipeline` is type-hinted against these
   abstractions, not concrete classes - genuine Dependency Inversion.
2. **A second implementation of every swappable role**, proving Liskov
   Substitution instead of just asserting it:
   - `ParquetDataSource` and `CsvDataSource` (`src/datasource.py`)
   - `CsvJsonReportWriter` and `ParquetReportWriter` (`src/writer.py`)
   - `tests/test_liskov_substitution.py` runs the *same* pipeline with
     each pairing and asserts identical results.
3. **Fixed a DRY violation**: `REQUIRED_COLUMNS` was previously defined
   twice (in `ParquetDataSource` and again inline in `TripDataValidator`).
   It now lives once, in `src/constants.py`.
4. **Fixed a code-cleanliness issue**: `pipeline.py` previously imported
   `pandas` at the bottom of the file after the class definition. The
   import is now at the top, where PEP 8 and the report's own "readable
   formatting" claim expect it to be.
5. **A custom exception hierarchy** (`src/exceptions.py`): `SchemaError`
   and `EmptySourceError` replace a bare `ValueError`.
6. **Test coverage now matches what the report claims**: schema, date,
   distance and fare validation; hourly/zone aggregation against a
   controlled sample; substitutability of both DataSource and
   ReportWriter implementations; and a full pipeline run using in-memory
   fakes. 15 tests, all passing (`execution_evidence.log`).
7. **Actually run, with real evidence included**: `data/generate_sample.py`
   creates a 1,000,000-row, schema-accurate sample (real TLC files are
   several hundred MB-several GB and are hosted on nyc.gov/AWS, outside
   this build environment's network access - see the script's docstring
   for how to substitute the real file with zero code changes). The
   `output/` folder in this submission contains the actual CSV/JSON
   report produced by running the app against that sample, and
   `execution_evidence.log` is a full transcript of the test run and two
   application runs (Parquet→CSV/JSON and CSV→Parquet, to demonstrate the
   OCP/LSP swap live).

## Run it
```bash
pip install -r requirements.txt
python3 data/generate_sample.py                 # regenerate the sample dataset
python3 -m pytest tests/ -v                      # 15 tests
python3 app.py --input data/sample_trip_data.parquet --output output
python3 app.py --input data/sample_trip_data_small.csv --output output2 --output-format parquet
```

To run against the real dataset: download any monthly file from the TLC
link above and pass its path to `--input` - no code changes required.

## Result (1,000,000-row sample, 1.5% invalid rows injected)
```json
{
  "total_trips_processed": 985000,
  "peak_hour": 2,
  "peak_hour_trip_count": 41456,
  "top_pickup_zone": 234
}
```

## Architecture
```
app.py                       <- composition root (only place concrete classes are wired)
src/interfaces.py            <- abstractions: DataSource, Validator, Transformer,
                                 Analytics, ReportWriter
src/datasource.py            <- ParquetDataSource, CsvDataSource
src/validation.py            <- TripDataValidator
src/transform.py             <- TripDataTransformer
src/analytics.py             <- DemandAnalytics
src/writer.py                <- CsvJsonReportWriter, ParquetReportWriter
src/pipeline.py               <- TaxiDemandPipeline (orchestrator)
src/constants.py, exceptions.py
data/generate_sample.py      <- builds the schema-accurate sample dataset
tests/                        <- 15 pytest tests (all passing)
output/                       <- real output from running against the sample
execution_evidence.log       <- full transcript of tests + app runs
```

See `docs/Task3_Report.docx` for the full write-up mapping SOLID
principles and clean-coding techniques to this code (LO3 AC 3.1, 3.2).

---

## Task 4 - Automated DevSecOps Testing

This project now includes a full staged, automated test pipeline covering
SCA, SAST, unit/integration testing and DAST, plus a GitHub Actions CI/CD
workflow that runs the same stages on every push.

**Quick start:**
```bash
pip install -r requirements.txt pip-audit bandit
python3 -m pytest tests/ -v              # 21 tests
./security/run_pipeline.sh               # full 5-stage pipeline -> PASS
./security/run_pipeline.sh --fail-demo   # same pipeline, deliberately flawed -> FAILS at SCA
```

See `security/TEST_SPECIFICATION.md` for what each stage checks, and
`execution_evidence.log` for a full transcript of every stage run in both
pass and fail configurations. `docs/Task4_Report.docx` is the accompanying
write-up (LO3 AC 3.3, 3.4, 3M1).

**To get real GitHub Actions screenshots:** push this folder to a new
GitHub repository - `.github/workflows/ci-cd.yml` will run automatically.
Trigger it once normally (green run across all 6 jobs), then trigger it
again via the Actions tab with "Run workflow" → `fail_demo: true` (red run,
stopping at the SCA or SAST job) for the success/failure contrast 3M1 asks for.
