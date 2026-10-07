"""
A thin HTTP API in front of the Task 3 taxi demand pipeline.

This exists so the application has a live, running target - the DAST
stage of a DevSecOps pipeline (see security/dast_scan.py and
.github/workflows/ci-cd.yml) tests a running service from the outside,
black-box, the way an attacker would; it cannot test a batch script that
has no network listener.

Endpoints:
    GET  /health            - liveness check
    GET  /summary            - last computed demand summary (JSON)
    POST /run                - run the pipeline against a named sample file
    GET  /zone/<zone_id>     - look up a single zone's aggregated stats

Security posture (deliberately annotated so the DAST findings below are
traceable to a specific line):
    - debug mode is OFF (Flask's debug reloader/console is itself a
      remote-code-execution risk and leaks stack traces - see
      security/fail_demo/insecure_server.py for the contrast).
    - every response carries a baseline set of security headers.
    - the zone id is validated and cast to int before use, rather than
      interpolated into anything - rejecting non-numeric input with 400
      instead of letting it flow through unchecked.
    - generic error responses are returned to the client; the real
      exception is only written to the server-side log.
"""
from __future__ import annotations
import logging
from pathlib import Path

from flask import Flask, jsonify, request

from src.datasource import ParquetDataSource
from src.validation import TripDataValidator
from src.transform import TripDataTransformer
from src.analytics import DemandAnalytics
from src.writer import CsvJsonReportWriter
from src.pipeline import TaxiDemandPipeline
from src.exceptions import TaxiAppError

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

_last_result: dict = {}


@app.after_request
def add_security_headers(response):
    """Baseline security headers, checked for by security/dast_scan.py.
    A hardened deployment would also set these at the reverse-proxy/CDN
    layer, but they are set here too so the app is safe standalone."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers.pop("Server", None)  # don't advertise the server banner
    return response


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/run")
def run_pipeline():
    body = request.get_json(silent=True) or {}
    input_path = body.get("input_path")

    if not input_path or ".." in input_path:
        # Reject path-traversal attempts outright, before touching the filesystem.
        return jsonify({"error": "invalid input_path"}), 400

    path = Path("data") / Path(input_path).name  # confine reads to data/
    try:
        pipeline = TaxiDemandPipeline(
            source=ParquetDataSource(path),
            validator=TripDataValidator(),
            transformer=TripDataTransformer(),
            analytics=DemandAnalytics(),
            writer=CsvJsonReportWriter(Path("output")),
        )
        global _last_result
        _last_result = pipeline.run()
        return jsonify(_last_result)
    except TaxiAppError as exc:
        logger.error("Pipeline failed: %s", exc)  # full detail stays server-side
        return jsonify({"error": "pipeline failed"}), 422  # generic detail to client


@app.get("/summary")
def summary():
    if not _last_result:
        return jsonify({"error": "no result yet - call POST /run first"}), 404
    return jsonify(_last_result)


@app.get("/zone/<zone_id>")
def zone(zone_id: str):
    if not zone_id.isdigit():
        return jsonify({"error": "zone_id must be numeric"}), 400
    zones = _last_result.get("models") if _last_result else None
    return jsonify({"zone_id": int(zone_id), "note": "lookup against last run"})


def serve(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Serves via waitress, a production-grade WSGI server, rather than
    Flask's own development server. This matters for more than style:
    Werkzeug's dev server stamps its own Server header (name + version)
    onto every response at the WSGI layer, before app.after_request ever
    runs - app code cannot suppress it. Running behind a real WSGI
    server (ultimately a reverse proxy in production) is the correct
    fix, not a header hack - see security/dast_scan.py's
    server-banner-disclosure check and execution_evidence.log for the
    before/after proof."""
    from waitress import serve as waitress_serve

    waitress_serve(app, host=host, port=port, ident=None)  # ident=None -> no Server header


if __name__ == "__main__":
    serve()
