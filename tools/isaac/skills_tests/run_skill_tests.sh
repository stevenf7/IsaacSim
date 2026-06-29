#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Discovery-driven test runner for skills/ scripts and snippets.
#   ./run_skill_tests.sh [all|static|unit|remote|standalone] [extra pytest args]   (default: all)
#
# The suite auto-discovers every script and snippet under skills/ and executes
# them by kind (no per-script wrappers). A test whose prerequisite is missing
# (no running python_server, no Isaac build, a missing dependency) FAILS with a
# description of how to enable it -- it is never silently skipped. The runner
# never stops on first failure and prints a full pass/fail list at the end.
#
# CI runs the full suite (`all`): CI machines build the repo, launch the sim, and
# have a GPU, so every prerequisite is present. There is no reduced "CI subset" --
# anything genuinely missing surfaces as a failure with remediation. The single-
# tier selectors below exist only for faster local iteration.
#
# Tiers:
#   static     - script + snippet syntax, frontmatter, cross-refs, coverage map (no runtime)
#   unit       - pure scripts (import + --help) and behavioral unit tests (no sim / GPU)
#   remote     - remote scripts via the python_server  (autostarts a headless sim if down)
#   standalone - standalone SimulationApp runs + shell + ros2 (fails w/ build steps if absent)
#   all        - everything (default)
#
# Env:
#   ISAACSIM_HOST / ISAACSIM_PORT  select the python_server (default 127.0.0.1:8226)
#   ISAACSIM_AUTOSTART=0           do not let the remote tier launch its own headless sim
#                                  (default: on -- launches one when none is reachable and a build exists)
#   ISAACSIM_STARTUP_TIMEOUT=300   seconds to wait for an autostarted server to respond
#   SKIP_HEAVY=1                   opt out of heavy GPU renders (local only; CI leaves it unset)
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIER="${1:-all}"
shift || true

# anyio's pytest plugin (if globally installed) is incompatible with pytest 6.x.
# -rA prints the full per-test pass/fail/skip list; --tb=short keeps failures readable.
PYTEST=(python3 -m pytest -c "$HERE/pytest.ini" -p no:anyio -rA --tb=short)

case "$TIER" in
    static)     "${PYTEST[@]}" "$HERE/static" "$@" ;;
    unit)       "${PYTEST[@]}" "$HERE/unit" "$@" ;;
    remote)     "${PYTEST[@]}" "$HERE/remote" "$@" ;;
    standalone) "${PYTEST[@]}" "$HERE/standalone" "$@" ;;
    all)        "${PYTEST[@]}" "$HERE/static" "$HERE/unit" "$HERE/remote" "$HERE/standalone" "$@" ;;
    *) echo "usage: $0 [all|static|unit|remote|standalone] [pytest args]" >&2; exit 2 ;;
esac
