#!/bin/bash
# Process omniperf benchmark results and upload to database.
# Called from omniperf-result-handler CI job.
#
# Required environment variables:
#   OMNIPERF_RESULT_HANDLER_TYPE - handler type (e.g. "isaac-sim")
#   OMNIPERF_RESULT_PATH         - path to omniperf results directory
#   CI_PROJECT_DIR               - GitLab CI project directory
#
# Optional environment variables:
#   OMNIPERF_BENCHMARK_REF - omniperf-benchmark repo ref (default: main)
#   CI_SERVER_HOST         - GitLab host (default: gitlab-master.nvidia.com)
#   CI_JOB_TOKEN           - GitLab CI job token
#   GITLAB_READ_TOKEN      - fallback GitLab read token

set -euo pipefail

echo "Initializing result handler processing"
echo "Handler type: $OMNIPERF_RESULT_HANDLER_TYPE"
echo "Result path: $OMNIPERF_RESULT_PATH"

if [ ! -d "$OMNIPERF_RESULT_PATH" ]; then
  echo "ERROR: $OMNIPERF_RESULT_PATH directory not found"
  ls -la
  exit 1
fi

mkdir -p outputs

# Clone omniperf-benchmark services for poetry + handler
SRV_DIR="services"
if [ ! -d "$SRV_DIR" ]; then
  REF="${OMNIPERF_BENCHMARK_REF:-main}"
  HOST="${CI_SERVER_HOST:-gitlab-master.nvidia.com}"
  [ -n "${CI_JOB_TOKEN:-}" ] && git clone --depth 1 --branch "$REF" "https://gitlab-ci-token:${CI_JOB_TOKEN}@${HOST}/omniverse/benchmark/omniperf-benchmark.git" repo_clone
  [ ! -d "repo_clone" ] && [ -n "${GITLAB_READ_TOKEN:-}" ] && git clone --depth 1 --branch "$REF" "https://${GITLAB_READ_TOKEN}@${HOST}/omniverse/benchmark/omniperf-benchmark.git" repo_clone
  [ -d "repo_clone/services" ] && SRV_DIR="repo_clone/services"
fi

cd "$SRV_DIR"
poetry install
cd "${CI_PROJECT_DIR}"

# Process each run directory
for run_dir in ${OMNIPERF_RESULT_PATH}/run_*/; do
  if [ -d "$run_dir" ]; then
    echo "Processing results from $run_dir"
    rm -rf outputs/run_results
    cp -r "$run_dir" outputs/run_results
    if ! (cd "$SRV_DIR" && poetry run omniperf_result_handler process --handler "$OMNIPERF_RESULT_HANDLER_TYPE" "${CI_PROJECT_DIR}/outputs/run_results" --ignore-account --upload-to-db --db-table omni_runtime_isaac_sim_mr_v1); then
      echo "WARNING: Result handler failed for $run_dir"
    fi
  fi
done

echo "Processing completed"
