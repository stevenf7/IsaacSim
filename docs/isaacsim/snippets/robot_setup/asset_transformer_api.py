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
Asset Transformer API snippets for the API reference doc.

Each snippet is a function; the docs use literalinclude with start-after/end-before
markers. When run as a script, SimulationApp and extensions are started, then the
orchestrator runs testable snippets with Evobot and temp dirs.
"""

from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

# -----------------------------------------------------------------------------
# Snippet: Rule Interface (conceptual signature)
# -----------------------------------------------------------------------------


def snippet_rule_interface():
    # <start-rule-interface-snippet>
    from abc import ABC, abstractmethod
    from typing import Any

    from pxr import Usd

    class RuleInterface(ABC):
        def __init__(
            self,
            source_stage: Usd.Stage,
            package_root: str,
            destination_path: str,
            args: dict[str, Any],
        ) -> None: ...

        @abstractmethod
        def process_rule(self) -> str | None:
            """Execute the rule logic. Return a stage path to switch stages, or None."""
            ...

        @abstractmethod
        def get_configuration_parameters(self) -> list:
            """Return the configuration parameters for this rule."""
            ...

        def log_operation(self, message: str) -> None:
            """Append a message to the operation log."""
            ...

        def add_affected_stage(self, stage_identifier: str) -> None:
            """Record an identifier for a stage affected by this rule."""
            ...

    # <end-rule-interface-snippet>
    pass


# -----------------------------------------------------------------------------
# Snippet: Rule logging (process_rule with log_operation)
# -----------------------------------------------------------------------------


def snippet_process_rule_logging():
    # <start-process-rule-logging-snippet>
    def process_rule(self) -> str | None:
        self.log_operation("SchemaRoutingRule start destination=payloads/physics.usda")
        self.log_operation("Schema patterns: Physics*, Physx*")

        # ... processing ...

        self.log_operation("Moved 5 schema(s) from /World/Robot: PhysicsRigidBodyAPI, PhysicsMassAPI, ...")
        self.log_operation("Processed 12 prim(s), moved 24 schema instance(s)")
        self.log_operation("SchemaRoutingRule completed")

    # <end-process-rule-logging-snippet>
    pass


# -----------------------------------------------------------------------------
# Snippet: Complete custom rule example
# -----------------------------------------------------------------------------


def snippet_custom_rule_example():
    # <start-custom-rule-example-snippet>
    from isaacsim.asset.transformer import RuleConfigurationParam, RuleInterface, RuleRegistry
    from pxr import Usd

    class MyCustomRule(RuleInterface):
        """A custom transformation rule."""

        def get_configuration_parameters(self) -> list:
            return [
                RuleConfigurationParam(
                    name="my_param",
                    display_name="My Parameter",
                    param_type=str,
                    description="Description of the parameter",
                    default_value="default_value",
                ),
                RuleConfigurationParam(
                    name="scope",
                    display_name="Scope",
                    param_type=str,
                    description="Root prim path to process",
                    default_value="/",
                ),
            ]

        def process_rule(self) -> str | None:
            params = self.args.get("params", {}) or {}
            my_param = params.get("my_param", "default_value")
            scope = params.get("scope", "/")

            self.log_operation(f"MyCustomRule start my_param={my_param} scope={scope}")
            stage = self.source_stage

            scope_prim = stage.GetPrimAtPath(scope)
            if not scope_prim.IsValid():
                self.log_operation(f"Scope prim not found: {scope}")
                return None

            processed_count = 0
            for prim in Usd.PrimRange(scope_prim):
                processed_count += 1

            self.log_operation(f"Processed {processed_count} prim(s)")
            self.log_operation("MyCustomRule completed")
            self.add_affected_stage("my_output.usda")

            return None

    registry = RuleRegistry()
    registry.register(MyCustomRule)
    # <end-custom-rule-example-snippet>


# -----------------------------------------------------------------------------
# Snippet: RuleSpec example
# -----------------------------------------------------------------------------


def snippet_rule_spec():
    # <start-rule-spec-snippet>
    from isaacsim.asset.transformer import RuleSpec

    # type = fully qualified class name used when registering the rule
    rule_spec = RuleSpec(
        name="My Custom Transformation",
        type="my_extension.rules.MyCustomRule",
        destination="payloads",
        params={"my_param": "custom_value", "scope": "/World/Robot"},
        enabled=True,
    )
    # <end-rule-spec-snippet>
    return rule_spec


# -----------------------------------------------------------------------------
# Snippet: Extension-based registration
# -----------------------------------------------------------------------------


def snippet_extension_registration():
    # <start-extension-registration-snippet>
    import omni.ext
    from isaacsim.asset.transformer import RuleRegistry

    from .rules import AnotherRule, MyCustomRule

    class MyExtension(omni.ext.IExt):
        def on_startup(self, ext_id):
            registry = RuleRegistry()
            registry.register(MyCustomRule)
            registry.register(AnotherRule)

        def on_shutdown(self):
            pass

    # <end-extension-registration-snippet>
    pass


# -----------------------------------------------------------------------------
# Snippet: Basic usage (profile + manager.run)
# -----------------------------------------------------------------------------


def snippet_basic_usage(input_stage_path: str, package_root: str):
    # <start-basic-usage-snippet>
    from isaacsim.asset.transformer import (
        AssetTransformerManager,
        RuleProfile,
        RuleSpec,
    )

    # input_stage_path = "/path/to/robot.usd"
    # package_root = "/output/robot_package"

    profile = RuleProfile(
        profile_name="My Transform Profile",
        version="1.0",
        rules=[
            RuleSpec(
                name="Route Physics Schemas",
                type="isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule",
                destination="payloads/Physics",
                params={
                    "schemas": ["Physics*", "Physx*"],
                    "stage_name": "physics.usda",
                },
                enabled=True,
            ),
            RuleSpec(
                name="Route Materials",
                type="isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule",
                destination="payloads",
                params={
                    "materials_layer": "materials.usda",
                    "deduplicate": True,
                },
                enabled=True,
            ),
        ],
    )

    manager = AssetTransformerManager()
    report = manager.run(
        input_stage_path=input_stage_path,
        profile=profile,
        package_root=package_root,
    )

    print(f"Transform completed: {report.output_stage_path}")
    for result in report.results:
        status = "SUCCESS" if result.success else "FAILED"
        print(f"  {result.rule.name}: {status}")
        if result.error:
            print(f"    Error: {result.error}")
    # <end-basic-usage-snippet>
    return report


# -----------------------------------------------------------------------------
# Snippet: Loading a profile from JSON
# -----------------------------------------------------------------------------


def snippet_load_profile_from_json(
    profile_path: str,
    input_stage_path: str,
    package_root: str,
):
    # <start-load-profile-from-json-snippet>
    import json

    from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

    # profile_path = "/path/to/profile.json"
    # input_stage_path = "/path/to/robot.usd"
    # package_root = "/output/robot_package"

    with open(profile_path, "r") as f:
        profile_data = json.load(f)

    profile = RuleProfile.from_dict(profile_data)

    manager = AssetTransformerManager()
    report = manager.run(
        input_stage_path=input_stage_path,
        profile=profile,
        package_root=package_root,
    )
    # <end-load-profile-from-json-snippet>
    return report


# -----------------------------------------------------------------------------
# Snippet: Saving the execution report
# -----------------------------------------------------------------------------


def snippet_save_execution_report(report):
    # <start-save-execution-report-snippet>
    import json

    # report = manager.run(input_stage_path, profile, package_root)

    report_path = f"{report.package_root}/transform_report.json"
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    # <end-save-execution-report-snippet>
    return report_path


# -----------------------------------------------------------------------------
# Snippet: Accessing rule logs
# -----------------------------------------------------------------------------


def snippet_accessing_rule_logs(report):
    # <start-accessing-rule-logs-snippet>
    # Iterate through rule results
    for result in report.results:
        print(f"\n=== {result.rule.name} ===")
        print(f"Type: {result.rule.type}")
        print(f"Success: {result.success}")
        print(f"Duration: {result.started_at} to {result.finished_at}")
        print(f"Affected stages: {result.affected_stages}")

        print("Log:")
        for entry in result.log:
            print(f"  {entry['message']}")
    # <end-accessing-rule-logs-snippet>


# -----------------------------------------------------------------------------
# Snippet: Querying registered rules
# -----------------------------------------------------------------------------


def snippet_querying_registered_rules():
    # <start-querying-registered-rules-snippet>
    from isaacsim.asset.transformer import RuleRegistry

    registry = RuleRegistry()
    rule_types = registry.list_rule_types()
    for rule_type in rule_types:
        print(rule_type)

    rule_cls = registry.get("isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule")
    if rule_cls:
        temp_rule = rule_cls.__new__(rule_cls)
        temp_rule._log = []
        params = temp_rule.get_configuration_parameters()
        for param in params:
            print(f"  {param.name}: {param.param_type.__name__} = {param.default_value}")
    # <end-querying-registered-rules-snippet>


# -----------------------------------------------------------------------------
# Snippet: Error handling
# -----------------------------------------------------------------------------


def snippet_error_handling(input_stage_path: str, profile, package_root: str):
    # <start-error-handling-snippet>
    from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

    # input_stage_path, profile, package_root from your context

    manager = AssetTransformerManager()

    try:
        report = manager.run(input_stage_path, profile, package_root)
    except RuntimeError as e:
        print(f"Transformation failed to start: {e}")
        raise

    for result in report.results:
        if not result.success:
            print(f"Rule '{result.rule.name}' failed: {result.error}")
    # <end-error-handling-snippet>
    return report


# -----------------------------------------------------------------------------
# Orchestrator and main (structure aligned with asset_transformer_tutorials.py)
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
    """Path to the built-in Isaac Sim Structure profile. Requires extensions to be loaded first."""
    from isaacsim.core.utils.extensions import get_extension_path_from_name

    ext_path = get_extension_path_from_name("isaacsim.asset.transformer.rules")
    if not ext_path:
        raise RuntimeError(
            "isaacsim.asset.transformer.rules extension not found; ensure it is loaded before resolving profile path."
        )
    return str(Path(ext_path) / "data" / "isaacsim_structure.json")


def _validate_report(report, step_name: str) -> None:
    """Raise if any rule in the report failed; used to validate snippet success."""
    failed = [r for r in report.results if not r.success]
    if failed:
        for r in failed:
            print(f"  Rule '{r.rule.name}' failed: {r.error}", file=sys.stderr)
        raise RuntimeError(f"{step_name}: {len(failed)} rule(s) failed")


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
    """Run all API snippets with Evobot and temp dirs. Called after SimulationApp is up."""
    input_stage_path, package_root_1 = _get_evobot_input_and_temp_output()
    print(f"Input (Evobot): {input_stage_path}")
    print(f"Temp outputs: {package_root_1} ...")
    sys.stdout.flush()

    profile_path = _get_builtin_profile_path()

    print("Snippet: Querying registered rules...")
    _run_step("snippet (querying registered rules)", snippet_querying_registered_rules)
    print()

    print("Snippet: Basic usage (profile + run)...")
    sys.stdout.flush()
    report = _run_step(
        "snippet (basic usage)",
        snippet_basic_usage,
        input_stage_path,
        package_root_1,
    )
    _validate_report(report, "snippet (basic usage)")
    _run_step("snippet (save execution report)", snippet_save_execution_report, report)
    print()

    print("Snippet: Accessing rule logs...")
    sys.stdout.flush()
    _run_step("snippet (accessing rule logs)", snippet_accessing_rule_logs, report)
    print()

    _, package_root_2 = _get_evobot_input_and_temp_output()
    print("Snippet: Load profile from JSON and run...")
    sys.stdout.flush()
    report2 = _run_step(
        "snippet (load profile from JSON)",
        snippet_load_profile_from_json,
        profile_path,
        input_stage_path,
        package_root_2,
    )
    _validate_report(report2, "snippet (load profile from JSON)")
    print()

    print("Snippet: Error handling (check results)...")
    sys.stdout.flush()
    from isaacsim.asset.transformer import RuleProfile

    with open(profile_path, "r") as f:
        profile = RuleProfile.from_dict(json.load(f))
    report3 = _run_step(
        "snippet (error handling)",
        snippet_error_handling,
        input_stage_path,
        profile,
        package_root_2,
    )
    _validate_report(report3, "snippet (error handling)")

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
