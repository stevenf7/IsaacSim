# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
Asset Transformer API examples for Tutorial 5.

Each snippet is a function; the docs use literalinclude with start-after/end-before
markers on the function bodies. When run as a script, SimulationApp is started,
then the orchestrator runs each snippet with Evobot from the assets library and
OS temp output dirs.
"""

from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

# -----------------------------------------------------------------------------
# Snippet 1: Load and Run a Saved Profile
# -----------------------------------------------------------------------------


def snippet_1_load_and_run_saved_profile(
    profile_path: str,
    input_stage_path: str,
    package_root: str,
):
    # <start-load-and-run-saved-profile-snippet>
    import json

    from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

    # profile_path = "/path/to/my_custom_profile.json"
    # input_stage_path = "/path/to/my_robot.usd"
    # package_root = "/output/my_robot_package"
    # Load a saved profile from disk
    with open(profile_path, "r") as f:
        profile_data = json.load(f)

    profile = RuleProfile.from_dict(profile_data)

    # Create the manager and run the transformation
    manager = AssetTransformerManager()
    report = manager.run(
        input_stage_path=input_stage_path,
        profile=profile,
        package_root=package_root,
    )

    # Inspect results
    print(f"Output asset: {report.output_stage_path}")
    for result in report.results:
        status = "OK" if result.success else "FAILED"
        print(f"  [{status}] {result.rule.name}")
        if result.error:
            print(f"    Error: {result.error}")
    # <end-load-and-run-saved-profile-snippet>
    return report


# -----------------------------------------------------------------------------
# Snippet 2: Build a Profile Programmatically
# -----------------------------------------------------------------------------


def snippet_2_build_profile_programmatically(
    input_stage_path: str,
    package_root: str,
):
    # <start-build-profile-programmatically-snippet>
    from isaacsim.asset.transformer import (
        AssetTransformerManager,
        RuleProfile,
        RuleSpec,
    )

    # input_stage_path = "/path/to/my_robot.usd"
    # package_root = "/output/my_robot_package"

    profile = RuleProfile(
        profile_name="Code-Defined Profile",
        version="1.0",
        base_name="base.usd",
        flatten_source=False,
        rules=[
            RuleSpec(
                name="Route Physics Schemas",
                type="isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule",
                destination="payloads/Physics",
                params={
                    "stage_name": "physics.usda",
                    "schemas": ["Physics*", "Newton*"],
                },
            ),
            RuleSpec(
                name="Route Materials",
                type="isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule",
                destination="payloads",
                params={
                    "materials_layer": "materials.usda",
                    "assets_folder": "Textures",
                    "download_textures": True,
                },
            ),
            RuleSpec(
                name="Deduplicate Geometries",
                type="isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule",
                destination="payloads",
                params={
                    "geometries_layer": "geometries.usd",
                    "instance_layer": "instances.usda",
                    "deduplicate": True,
                },
            ),
        ],
    )

    manager = AssetTransformerManager()
    report = manager.run(
        input_stage_path=input_stage_path,
        profile=profile,
        package_root=package_root,
    )

    print(f"Transformation complete: {report.output_stage_path}")
    # <end-build-profile-programmatically-snippet>
    return report


# -----------------------------------------------------------------------------
# Snippet 3: Use the Isaac Sim Structure Profile in Code
# -----------------------------------------------------------------------------


def snippet_3_use_isaac_sim_structure_profile(
    input_stage_path: str,
    package_root: str,
):
    # <start-use-isaac-sim-structure-profile-snippet>
    import json
    from pathlib import Path

    from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile
    from isaacsim.core.utils.extensions import get_extension_path_from_name

    # input_stage_path = "/path/to/my_robot.usd"
    # package_root = "/output/my_robot_isaacsim_structure"
    # Locate the built-in profile shipped with the rules extension (use get_extension_path_from_name so the path is absolute)
    ext_path = Path(get_extension_path_from_name("isaacsim.asset.transformer.rules"))
    profile_path = ext_path / "data" / "isaacsim_structure.json"

    with open(profile_path, "r") as f:
        profile = RuleProfile.from_dict(json.load(f))

    manager = AssetTransformerManager()
    report = manager.run(
        input_stage_path=input_stage_path,
        profile=profile,
        package_root=package_root,
    )
    # <end-use-isaac-sim-structure-profile-snippet>
    return report


# -----------------------------------------------------------------------------
# Snippet 4: Batch-Process Multiple Assets
# -----------------------------------------------------------------------------


def snippet_4_batch_process_multiple_assets(
    profile_path: str,
    asset_paths: list[str],
    output_base_dir: str,
):
    # <start-batch-process-multiple-assets-snippet>
    import json
    from pathlib import Path

    from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

    # profile_path = "/path/to/my_custom_profile.json"
    # asset_paths = ["/assets/robot_a.usd", "/assets/robot_b.usd", "/assets/robot_c.usd"]
    # output_base_dir = "/output"

    with open(profile_path, "r") as f:
        profile = RuleProfile.from_dict(json.load(f))

    manager = AssetTransformerManager()

    for asset_path in asset_paths:
        asset_name = Path(asset_path).stem
        output_dir = f"{output_base_dir.rstrip('/')}/{asset_name}_transformed"

        report = manager.run(
            input_stage_path=asset_path,
            profile=profile,
            package_root=output_dir,
        )

        all_ok = all(r.success for r in report.results)
        print(f"{asset_name}: {'PASS' if all_ok else 'FAIL'} -> {report.output_stage_path}")
    # <end-batch-process-multiple-assets-snippet>


# -----------------------------------------------------------------------------
# Snippet 5: Save and Inspect the Execution Report
# -----------------------------------------------------------------------------


def snippet_5_save_report(report):
    # <start-save-and-inspect-report-snippet>
    import json
    from pathlib import Path

    # report = <ExecutionReport from manager.run() in any example above>
    # After running the transformation (report from any example above)
    report_path = Path(report.package_root) / "transform_report.json"
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    print(f"Report saved to: {report_path}")
    # <end-save-and-inspect-report-snippet>
    return report_path


# -----------------------------------------------------------------------------
# Snippet 6: Discover Available Rule Types
# -----------------------------------------------------------------------------


def snippet_6_discover_rule_types():
    # <start-discover-available-rule-types-snippet>
    from isaacsim.asset.transformer import RuleRegistry

    registry = RuleRegistry()
    for rule_type in registry.list_rule_types():
        print(rule_type)
    # <end-discover-available-rule-types-snippet>


# -----------------------------------------------------------------------------
# Orchestrator and main
# -----------------------------------------------------------------------------

EVOBOT_REL_PATH = "/Isaac/Robots/Fraunhofer/Evobot/evobot.usd"


def _get_evobot_input_and_temp_output():
    """Resolve Evobot path from assets root and create a temp output dir."""
    from isaacsim.storage.native import get_assets_root_path

    assets_root = get_assets_root_path()
    if not assets_root:
        raise RuntimeError("Could not find Isaac Sim assets root (isaacsim.storage.native).")
    input_stage_path = assets_root.rstrip("/") + EVOBOT_REL_PATH
    package_root = tempfile.mkdtemp(prefix="asset_transformer_")
    return input_stage_path, package_root


def _ensure_asset_transformer_extensions_loaded(simulation_app):
    """Load asset transformer extensions so extension paths and rules are available. Call after SimulationApp is created."""
    from isaacsim.core.utils.extensions import enable_extension

    enable_extension("isaacsim.asset.transformer")
    enable_extension("isaacsim.asset.transformer.rules")
    simulation_app.update()


def _get_builtin_profile_path():
    """Path to the built-in Isaac Sim Structure profile (for snippet 1 and 4). Requires extensions to be loaded first."""
    from isaacsim.core.utils.extensions import get_extension_path_from_name

    ext_path = get_extension_path_from_name("isaacsim.asset.transformer.rules")
    if not ext_path:
        raise RuntimeError(
            "isaacsim.asset.transformer.rules extension not found; ensure it is loaded before resolving profile path."
        )
    return str(Path(ext_path) / "data" / "isaacsim_structure.json")


def _run_step(name: str, fn, *args, **kwargs):
    """Run a single step; on exception print traceback and re-raise."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[FAILED] {name}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


def run_orchestrator() -> int:
    """Run all snippets with Evobot and temp dirs. Called after SimulationApp is up."""
    input_stage_path, package_root_1 = _get_evobot_input_and_temp_output()
    print(f"Input (Evobot): {input_stage_path}")
    print(f"Temp outputs: {package_root_1} ...")
    sys.stdout.flush()

    print("Discovering available rule types...")
    _run_step("snippet_6 (discover rule types)", snippet_6_discover_rule_types)
    print()

    profile_path = _get_builtin_profile_path()
    print(f"Snippet 1: Loading and running saved profile from {profile_path}...")
    sys.stdout.flush()
    report = _run_step(
        "snippet_1 (load and run saved profile)",
        snippet_1_load_and_run_saved_profile,
        profile_path,
        input_stage_path,
        package_root_1,
    )
    _run_step("snippet_5 (save report)", snippet_5_save_report, report)
    print()

    _, package_root_2 = _get_evobot_input_and_temp_output()
    print("Snippet 2: Building profile programmatically and running transformation...")
    sys.stdout.flush()
    report = _run_step(
        "snippet_2 (build profile and run)",
        snippet_2_build_profile_programmatically,
        input_stage_path,
        package_root_2,
    )
    _run_step("snippet_5 (save report)", snippet_5_save_report, report)
    print()

    _, package_root_3 = _get_evobot_input_and_temp_output()
    print("Snippet 3: Using Isaac Sim Structure profile and running transformation...")
    sys.stdout.flush()
    report = _run_step(
        "snippet_3 (Isaac Sim Structure profile)",
        snippet_3_use_isaac_sim_structure_profile,
        input_stage_path,
        package_root_3,
    )
    _run_step("snippet_5 (save report)", snippet_5_save_report, report)
    print()

    print("Snippet 4: Batch-processing multiple assets...")
    sys.stdout.flush()
    output_base = tempfile.mkdtemp(prefix="asset_transformer_batch_")
    _run_step(
        "snippet_4 (batch process)",
        snippet_4_batch_process_multiple_assets,
        profile_path,
        [input_stage_path],
        output_base,
    )

    return 0


if __name__ == "__main__":
    try:
        from isaacsim import SimulationApp

        _simulation_app = SimulationApp({"headless": True})
    except ImportError:
        print("Isaac Sim not found. Run this script with Isaac Sim's python.sh.", file=sys.stderr)
        sys.exit(1)

    try:
        _ensure_asset_transformer_extensions_loaded(_simulation_app)

        run_orchestrator()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
    finally:
        _simulation_app.close()
