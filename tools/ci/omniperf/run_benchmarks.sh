#!/bin/bash
# Run omniperf benchmarks with retry logic and reggie regression detection.
# Called from test-linux-x86_64-omniperf-benchmarks-1-gpu CI job.
#
# Required environment variables:
#   REGGIE_BOOTSTRAP_REF  - reggie bootstrap git ref
#
# Optional environment variables:
#   MAX_RETRIES           - number of benchmark attempts (default: 3)

set -euo pipefail

MAX_RETRIES="${MAX_RETRIES:-3}"

# Unpack build artifacts
./repo.sh unzip_file --file _build/packages/isaac-sim-standalone*.7z --dst _build/linux-x86_64/release
echo "=== _build/packages/ ===" && ls -la _build/packages/
echo "=== _build/linux-x86_64/release/ ===" && ls -la _build/linux-x86_64/release/

export OMNI_USER='$omni-api-token'
export OMNI_PASS="$OMNIPERF_ISAAC_SIM_DEV_SERVER_PASS"

REGGIE_EXIT=0

for i in $(seq 1 "$MAX_RETRIES"); do
  echo "=== Omniperf benchmark iteration $i/$MAX_RETRIES ==="

  # Suppress reggie notifications for non-final iterations
  if [ "$i" -lt "$MAX_RETRIES" ]; then
    export REGGIE_SUPPRESS_NOTIFICATIONS=1
  else
    unset REGGIE_SUPPRESS_NOTIFICATIONS
  fi

  # 1. Run benchmark, output to per-run subdirectory
  if ! omniperf isaacsim \
    --local-app-path _build/linux-x86_64/release/isaac-sim.sh \
    --benchmark-type SINGLE_GPU_TEST \
    --output-path _omniperf_results/run_$i \
    --profiler-type tracy \
    --headless; then
    echo "Benchmark run $i failed, skipping reggie detect"
    continue
  fi

  # 2. Create per-run reggie config (copy base, replace artifacts_glob)
  sed "s|^artifacts_glob:.*|artifacts_glob: '_omniperf_results/run_${i}/WARM_*_reggie_results_1.json'|" \
    .reggie-omniperf.yml > .reggie-omniperf-run-$i.yml

  # 3. Run reggie detect with accumulated data
  REGGIE_EXIT=0
  set +e
  ./reggie-bootstrap-${REGGIE_BOOTSTRAP_REF}/.venv/bin/reggie detect \
    -P ".reggie-omniperf-run-$i.yml"
  REGGIE_EXIT=$?
  set -e

  # 4. Preserve reggie report for this iteration
  [ -d .reggie-out ] && cp -r .reggie-out/ .reggie-out-iter-$i/

  # 5. Evaluate result
  if [ "$REGGIE_EXIT" -eq 0 ]; then
    unset REGGIE_SUPPRESS_NOTIFICATIONS
    echo "No regressions detected at iteration $i, stopping."
    break
  elif [ "$REGGIE_EXIT" -ge 121 ] && [ "$REGGIE_EXIT" -le 124 ]; then
    echo "Regressions detected (exit $REGGIE_EXIT) at iteration $i/$MAX_RETRIES."
  else
    echo "Unexpected reggie error (exit $REGGIE_EXIT), aborting."
    exit $REGGIE_EXIT
  fi
done

exit $REGGIE_EXIT
