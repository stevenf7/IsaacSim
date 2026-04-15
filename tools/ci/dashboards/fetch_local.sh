#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# Fetch historical dashboard data from GitLab/GitHub and generate the
# dashboard HTML locally — no pipeline required.
#
# Works for both IsaacLab and IsaacSim dashboards.
#
# Usage (from omni_isaac_sim repo root):
#
#   export GITLAB_AUTH_TOKEN="glpat-..."
#
#   # IsaacLab (default):
#   ./tools/ci/dashboards/fetch_local.sh
#
#   # IsaacSim:
#   ./tools/ci/dashboards/fetch_local.sh --config tools/ci/dashboards/config_isaac_sim.yml --data-dir _isaacsim_cache
#
#   # Generate-only (skip fetch, useful for HTML/JS iteration):
#   ./tools/ci/dashboards/fetch_local.sh --skip-fetch
#
#   # More pipelines, verbose, force re-download:
#   ./tools/ci/dashboards/fetch_local.sh --max-runs 50 --verbose --force-refetch
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

# ── Defaults ──────────────────────────────────────────────────────────────────
CONFIG="tools/ci/dashboards/config_isaac_lab.yml"
DATA_DIR="_isaaclab_cache"
ISAAC_SIM_BRANCH="develop"
ISAAC_LAB_BRANCH="develop"
MAX_RUNS=5
GITHUB_MAX_RUNS=""
SKIP_FETCH=false
VERBOSE=false
FORCE_REFETCH=false

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)         CONFIG="$2"; shift 2 ;;
    --data-dir)       DATA_DIR="$2"; shift 2 ;;
    --branch)         ISAAC_SIM_BRANCH="$2"; shift 2 ;;
    --lab-branch)     ISAAC_LAB_BRANCH="$2"; shift 2 ;;
    --max-runs)       MAX_RUNS="$2"; shift 2 ;;
    --github-max-runs) GITHUB_MAX_RUNS="$2"; shift 2 ;;
    --skip-fetch)     SKIP_FETCH=true; shift ;;
    --verbose|-v)     VERBOSE=true; shift ;;
    --force-refetch)  FORCE_REFETCH=true; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --config FILE        Dashboard config YAML (default: config_isaac_lab.yml)"
      echo "  --data-dir DIR       Cache directory (default: _isaaclab_cache)"
      echo "  --branch NAME        Isaac Sim branch to fetch (default: develop)"
      echo "  --lab-branch NAME    IsaacLab branch for run records (default: develop)"
      echo "  --max-runs N         Max pipelines to fetch (default: 5)"
      echo "  --github-max-runs N  Max GitHub runs to fetch (default: same as --max-runs)"
      echo "  --skip-fetch         Skip fetch, only regenerate from cached data"
      echo "  --force-refetch      Re-download data for already-cached pipelines"
      echo "  --verbose, -v        Verbose output"
      echo ""
      echo "Environment:"
      echo "  GITLAB_AUTH_TOKEN    GitLab PAT with read_api scope (required unless --skip-fetch)"
      echo "  GITHUB_NVIDIA_DEV_TOKEN  GitHub PAT (optional, for GitHub workflow data)"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

GITHUB_MAX_RUNS="${GITHUB_MAX_RUNS:-$MAX_RUNS}"

# ── Python setup ─────────────────────────────────────────────────────────────
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

if [[ -z "${DASHBOARD_PYTHON:-}" ]]; then
  if [[ ! -x "$ROOT/.ci-dashboard-venv/bin/python" ]]; then
    echo "Creating venv at .ci-dashboard-venv (set DASHBOARD_PYTHON to use another interpreter)" >&2
    "$PY" -m venv .ci-dashboard-venv
  fi
  PY="$ROOT/.ci-dashboard-venv/bin/python"
fi
if ! "$PY" -c "import requests; import yaml" 2>/dev/null; then
  echo "Installing dependencies into selected Python…" >&2
  "$PY" -m pip install --quiet -r "$ROOT/tools/ci/requirements.txt" || { echo "Error: failed to install dependencies." >&2; exit 1; }
fi

# ── Build flag arrays ────────────────────────────────────────────────────────
VERBOSE_FLAG=()
$VERBOSE && VERBOSE_FLAG=(--verbose)

REFETCH_FLAG=()
$FORCE_REFETCH && REFETCH_FLAG=(--force-refetch)

echo "config=$CONFIG data-dir=$DATA_DIR branch=$ISAAC_SIM_BRANCH max-runs=$MAX_RUNS" >&2

# ── Fetch ────────────────────────────────────────────────────────────────────
if ! $SKIP_FETCH; then
  if [[ -z "${GITLAB_AUTH_TOKEN:-}${GITLAB_TOKEN:-}${GITLAB_API_TOKEN:-}" ]]; then
    echo "Set GITLAB_AUTH_TOKEN, GITLAB_TOKEN, or GITLAB_API_TOKEN to a GitLab PAT with read_api." >&2
    exit 1
  fi

  "$PY" tools/ci/dashboards/ci_dashboard.py \
    fetch-gitlab \
    --config "$CONFIG" \
    --isaac-sim-branch "$ISAAC_SIM_BRANCH" \
    --isaac-lab-branch "$ISAAC_LAB_BRANCH" \
    --max-runs "$MAX_RUNS" \
    --data-dir "$DATA_DIR" \
    "${VERBOSE_FLAG[@]}" \
    "${REFETCH_FLAG[@]}"

  "$PY" tools/ci/dashboards/ci_dashboard.py \
    fetch-github \
    --config "$CONFIG" \
    --github-max-runs "$GITHUB_MAX_RUNS" \
    --data-dir "$DATA_DIR" \
    "${VERBOSE_FLAG[@]}" \
    "${REFETCH_FLAG[@]}"
fi

# ── Generate ─────────────────────────────────────────────────────────────────
"$PY" tools/ci/dashboards/ci_dashboard.py \
  generate \
  --config "$CONFIG" \
  --data-dir "$DATA_DIR"

echo "" >&2
echo "Dashboard ready: $DATA_DIR/output/dashboard.html" >&2
