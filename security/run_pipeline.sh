#!/usr/bin/env bash
# Local staged DevSecOps test pipeline - mirrors .github/workflows/ci-cd.yml
# stage-for-stage, so it can be run and evidenced anywhere this project
# runs (including a sandbox with no GitHub Actions access), while the
# CI YAML is the authoritative, reproducible definition once pushed to
# a real GitHub repository.
#
# Stage order matters and is deliberate (cheapest/fastest checks first,
# so a bad build fails in seconds, not minutes):
#   1. SCA   - are our DEPENDENCIES safe?           (seconds, no app code touched)
#   2. SAST  - is our OWN CODE safe?                (seconds, static analysis)
#   3. Unit/integration tests - is the app CORRECT? (sub-second, no I/O)
#   4. Build - does it actually package/run?
#   5. DAST  - is the RUNNING app safe?             (slowest - spins up a real server)
#
# Each stage must pass before the next runs - exactly how `needs:` gates
# jobs in the GitHub Actions workflow.
#
# Usage:
#   ./security/run_pipeline.sh              -> full pipeline, all real code (expect PASS)
#   ./security/run_pipeline.sh --fail-demo  -> includes the deliberately
#                                              vulnerable dependency + code
#                                              (expect FAIL, with contrast)
set -uo pipefail

MODE="${1:-}"
FAIL_DEMO_FLAG=""
[[ "$MODE" == "--fail-demo" ]] && FAIL_DEMO_FLAG="--fail-demo"

STAGE_LOG="security/evidence/pipeline_run_$([[ -n "$FAIL_DEMO_FLAG" ]] && echo fail || echo pass).log"
mkdir -p security/evidence
: > "$STAGE_LOG"

run_stage() {
    local name="$1"; shift
    echo "" | tee -a "$STAGE_LOG"
    echo "##################################################" | tee -a "$STAGE_LOG"
    echo "# STAGE: $name" | tee -a "$STAGE_LOG"
    echo "##################################################" | tee -a "$STAGE_LOG"
    "$@" 2>&1 | tee -a "$STAGE_LOG"
    local status=${PIPESTATUS[0]}
    if [[ $status -ne 0 ]]; then
        echo "" | tee -a "$STAGE_LOG"
        echo "PIPELINE STOPPED: stage '$name' failed (exit $status). Later stages did not run." | tee -a "$STAGE_LOG"
        exit $status
    fi
    return 0
}

echo "DevSecOps pipeline starting - mode: ${MODE:-normal}" | tee -a "$STAGE_LOG"

if [[ -n "$FAIL_DEMO_FLAG" ]]; then
    run_stage "1/5 SCA (Software Composition Analysis)"      ./security/run_sca.sh --fail-demo
else
    run_stage "1/5 SCA (Software Composition Analysis)"      ./security/run_sca.sh
fi

if [[ -n "$FAIL_DEMO_FLAG" ]]; then
    run_stage "2/5 SAST (Static Application Security Testing)" ./security/run_sast.sh --fail-demo
else
    run_stage "2/5 SAST (Static Application Security Testing)" ./security/run_sast.sh
fi

run_stage "3/5 Unit and integration tests"                   python3 -m pytest tests/ -v

run_stage "4/5 Build check (package imports cleanly)"        python3 -c "import api.server; import src.pipeline; print('build OK: all modules import cleanly')"

run_stage "5/5 DAST (Dynamic Application Security Testing)"  python3 security/dast_scan.py $FAIL_DEMO_FLAG

echo "" | tee -a "$STAGE_LOG"
echo "PIPELINE PASSED: all 5 stages green. Safe to deploy." | tee -a "$STAGE_LOG"
