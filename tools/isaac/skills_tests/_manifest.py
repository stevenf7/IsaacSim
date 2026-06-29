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

"""Per-script run specs for the generic executors (data, not code).

Scripts NOT listed here fall back to safe defaults:
  - remote     : sent with no args; only status:ok is asserted.
  - standalone : run with no args (timeout 600s); exit 0 + no traceback asserted.
  - shell      : static `bash -n` only (no auto-execution).
  - pure       : imported; --help run only if listed in PURE_HELP.

Keys are paths relative to skills/. Adding a new script needs an entry here only
if it requires arguments, a scene, rendering, or a non-default assertion.
"""

from __future__ import annotations

# --- remote payloads (sent to the python_server) ------------------------------
# scene=True   -> requires the shared stage+cube fixture (CUBE path below)
# render=True  -> needs the renderer + isaacsim.test.utils (marked gpu)
# png/file     -> assert the named artifact was produced
# timeout=<s>  -> client wait for the server reply (default 180s); raise it for
#                 render captures, whose first frame on a cold/autostarted server
#                 pays one-time RTX shader-compilation cost.
CUBE = "/World/SkillTestCube"

BUILD_REMEDIATION = (
    "No Isaac Sim python launcher found.\n"
    "  To enable this test, build the repo (./build.sh --no-docker) so that\n"
    "  _build/linux-x86_64/release/python.sh exists, or set ISAAC_SIM_DIR to an\n"
    "  Isaac Sim install that contains python.sh."
)

REMOTE: dict[str, dict] = {
    "isaac-sim-remote/scripts/health_check.py": {"expect": "Health: OK"},
    "isaac-sim-remote/scripts/stage_info.py": {"scene": True, "expect": "SkillTestCube"},
    "isaac-sim-remote/scripts/open_stage.py": {"args": ["action=info"]},
    "isaac-sim-remote/scripts/select_prim.py": {"args": ["action=get"]},
    "isaac-sim-remote/scripts/prim_properties.py": {
        "args": [f"prim_path={CUBE}", "action=list"],
        "scene": True,
        "expect": "Attributes on",
    },
    "isaac-sim-remote/scripts/prim_transform.py": {
        "args": [f"prim_path={CUBE}", "action=get"],
        "scene": True,
        "expect": "Position",
    },
    "isaac-sim-remote/scripts/camera_control.py": {"args": ["action=get"], "scene": True, "expect": "Camera"},
    "isaac-sim-remote/scripts/simulation_control.py": {"args": ["action=status"], "expect": "state"},
    "isaac-sim-remote/scripts/console_log.py": {"args": ["action=path"], "expect": "Log file"},
    "isaac-sim-remote/scripts/execute_command.py": {"args": ["action=list", "filter=Mesh"], "expect": "Commands ("},
    "isaac-sim-remote/scripts/set_asset_root.py": {"expect": "asset root"},
    "isaac-sim-remote/scripts/viewport_screenshot.py": {
        "args": ["output_path=/tmp/sktest_vp.png"],
        "scene": True,
        "render": True,
        "png": "/tmp/sktest_vp.png",
        "timeout": 600.0,
    },
    "isaac-sim-remote/scripts/app_screenshot.py": {
        "args": ["output_path=/tmp/sktest_app.png"],
        "scene": True,
        "render": True,
        "png": "/tmp/sktest_app.png",
        "timeout": 600.0,
    },
    "isaac-sim-remote/scripts/capture_annotator.py": {
        "args": ["annotator=distance_to_camera", "output_path=/tmp/sktest_anno.npy"],
        "scene": True,
        "render": True,
        "file": "/tmp/sktest_anno.npy",
        "timeout": 600.0,
    },
}

# --- standalone SimulationApp scripts (run via the Isaac python launcher) ------
# {out} is substituted with a per-test temp directory.
STANDALONE: dict[str, dict] = {
    "data-collection-sim/scripts/warehouse_sdg.py": {
        "run_args": ["--num-frames", "2", "--output-dir", "{out}"],
        "expect_glob": "*.png",
        "timeout": 1800,
    },
}

# --- shell scripts ------------------------------------------------------------
# Every shell must be classified (the generic shell test fails for any shell with
# no entry). Options:
#   bespoke      -> behavior covered by a dedicated fixture-based test (named here)
#   static_only  -> launches a server/app or is a doc snippet; bash -n only
#   <run spec>   -> args + assertions (exit_nonzero/exit_zero/contains, env_unset)
SHELL: dict[str, dict] = {
    "isaac-sim-validator/scripts/validate_sim.sh": {"bespoke": "test_validate_sim_sh.py"},
    "data-collection-sim/scripts/validate_sdg_output.sh": {"bespoke": "test_validate_sdg_output_sh.py"},
    "validation-diff-gifs/scripts/generate_diff_gifs.sh": {"args": [], "exit_nonzero": True, "contains": "Usage"},
    "isaac-sim-ros2-bridge/scripts/prerequisites.sh": {
        "args": [],
        "env_unset": ["ISAAC_SIM_DIR"],
        "exit_nonzero": True,
        "contains": "ISAAC_SIM_DIR is not set",
    },
    "_internal/build-docs/scripts/serve_docs.sh": {
        "static_only": True,
        "reason": "long-running HTTP server; covered by bash -n. Run manually: bash serve_docs.sh [PORT]",
    },
    "isaac-sim-headless-deployment/scripts/kit_cli_with_script_execution.sh": {
        "static_only": True,
        "reason": "documentation snippet referencing placeholder scripts (my_script.py / physics_batch.py); "
        "covered by bash -n",
    },
}

# --- pure scripts that expose an argparse CLI (--help is exercised) ------------
PURE_HELP: dict[str, bool] = {
    "profile-isaac-sim/scripts/compare_tracy_csvs.py": True,
    "isaac-sim-remote/scripts/isaacsim_send.py": True,
}
