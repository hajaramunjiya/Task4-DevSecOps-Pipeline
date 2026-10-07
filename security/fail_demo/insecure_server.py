"""
INTENTIONALLY INSECURE - for demonstrating a FAILING DAST scan only.

This is a deliberately vulnerable twin of api/server.py, kept outside the
src/ and api/ packages so it is never imported by the real application or
by the CI "build" stage. It exists purely to give security/dast_scan.py
something genuine to fail against, to prove the DAST gate actually works
rather than only ever showing a green tick.

Differences from api/server.py, each one a real, exploitable issue:
    1. debug=True - Flask's Werkzeug debugger exposes a full interactive
       Python console on any unhandled exception. An attacker who
       triggers an error gets remote code execution, not just a stack
       trace.
    2. No security headers are set at all.
    3. The /zone/<zone_id> route builds a string and evaluates it with
       eval() - a textbook injection flaw, included only so SAST
       (bandit) and DAST both have a concrete, matched finding to catch.
    4. A hardcoded secret key, flagged by both SAST and SCA-adjacent
       secret scanning.
"""
from flask import Flask, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = "hardcoded-super-secret-123"


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/zone/<zone_id>")
def zone(zone_id: str):
    # Intentionally vulnerable: never do this. Lets an attacker run
    # arbitrary Python via the zone_id path segment, e.g. /zone/__import__('os').system('id')
    result = eval(f"{zone_id} if {zone_id}.isdigit() else None")
    return jsonify({"zone_id": result})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True, use_reloader=False)
