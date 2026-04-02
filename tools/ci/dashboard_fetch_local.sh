#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# Run the same GitLab fetch + optional GitHub fetch as the
# get-isaaclab-historical-data CI job, without waiting for a pipeline.
#
# Usage (from omni_isaac_sim repo root):
#
#   export GITLAB_AUTH_TOKEN="glpat-..."     # or GITLAB_TOKEN or GITLAB_API_TOKEN
#   export GITHUB_NVIDIA_DEV_TOKEN="ghp_..." # optional; or GITHUB_TOKEN or GITHUB_API_TOKEN
#   export ISAAC_SIM_BRANCH="develop"        # default: develop (match CI historical fetch)
#   export ISAAC_LAB_BRANCH="develop"        # default: develop
#   # optional:
#   # export DASHBOARD_MAX_RUNS=5            # default 5 for quick local runs
#   # export DASHBOARD_VERBOSE=1             # pass --verbose to the script
#   ./tools/ci/dashboard_fetch_local.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${DASHBOARD_PYTHON:-}"
if [[ -z "$PY" ]]; then
  if [[ -x "$ROOT/.ci-dashboard-venv/bin/python" ]]; then
    PY="$ROOT/.ci-dashboard-venv/bin/python"
  elif command -v python3.12 >/dev/null 2>&1; then
    PY="$(command -v python3.12)"
  else
    PY="$(command -v python3)"
  fi
fi

if [[ -z "${GITLAB_AUTH_TOKEN:-}${GITLAB_TOKEN:-}${GITLAB_API_TOKEN:-}" ]]; then
  echo "Set GITLAB_AUTH_TOKEN, GITLAB_TOKEN, or GITLAB_API_TOKEN to a GitLab PAT with read_api." >&2
  exit 1
fi

ISAAC_SIM_BRANCH="${ISAAC_SIM_BRANCH:-develop}"
ISAAC_LAB_BRANCH="${ISAAC_LAB_BRANCH:-develop}"
DATA_DIR="${DASHBOARD_DATA_DIR:-_dashboard_cache}"
MAX_RUNS="${DASHBOARD_MAX_RUNS:-5}"
GITHUB_MAX_RUNS="${DASHBOARD_GITHUB_MAX_RUNS:-$MAX_RUNS}"

# Optional: create venv like CI if no explicit interpreter and venv missing
if [[ -z "${DASHBOARD_PYTHON:-}" ]]; then
  if [[ ! -x "$ROOT/.ci-dashboard-venv/bin/python" ]]; then
    echo "Creating venv at .ci-dashboard-venv (set DASHBOARD_PYTHON to use another interpreter)" >&2
    "$PY" -m venv .ci-dashboard-venv
  fi
  PY="$ROOT/.ci-dashboard-venv/bin/python"
fi
if ! "$PY" -c "import requests" 2>/dev/null; then
  echo "Installing requests into selected Python…" >&2
  "$PY" -m pip install --quiet requests || { echo "Error: failed to install requests package." >&2; exit 1; }
fi

VERBOSE=()
if [[ "${DASHBOARD_VERBOSE:-0}" == "1" || "${DASHBOARD_VERBOSE:-}" == "true" ]]; then
  VERBOSE=(--verbose)
fi

echo "Using Python: $PY" >&2
echo "isaac-sim-branch=$ISAAC_SIM_BRANCH isaac-lab-branch=$ISAAC_LAB_BRANCH data-dir=$DATA_DIR max-runs=$MAX_RUNS" >&2

"$PY" tools/ci/isaac_lab_dashboard.py \
  fetch-gitlab \
  --isaac-sim-branch "$ISAAC_SIM_BRANCH" \
  --isaac-lab-branch "$ISAAC_LAB_BRANCH" \
  --max-runs "$MAX_RUNS" \
  --data-dir "$DATA_DIR" \
  "${VERBOSE[@]}"

"$PY" tools/ci/isaac_lab_dashboard.py \
  fetch-github \
  --github-max-runs "$GITHUB_MAX_RUNS" \
  --data-dir "$DATA_DIR" \
  "${VERBOSE[@]}"

exec "$PY" tools/ci/isaac_lab_dashboard.py \
  generate \
  --data-dir "$DATA_DIR"
