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
Mesh merge snippets for ext_isaacsim_util_merge_mesh.rst.

Each snippet is a function; the doc uses literalinclude with start-after/end-before
markers on the function bodies. When run as a script, SimulationApp is started, the
Scene Optimizer extension is enabled, then the orchestrator imports the bundled
carter.urdf test asset and exercises every snippet against the resulting USD stage.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import traceback

# -----------------------------------------------------------------------------
# Snippet: enable the Scene Optimizer extension from a standalone script
# -----------------------------------------------------------------------------


def snippet_enable_scene_optimizer():
    # <start-enable-scene-optimizer-snippet>
    import omni.kit.app

    omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("omni.scene.optimizer.core", True)
    # <end-enable-scene-optimizer-snippet>


# -----------------------------------------------------------------------------
# Snippet: full importer-equivalent pipeline applied to an existing stage
# -----------------------------------------------------------------------------


def snippet_full_pipeline(stage_path: str) -> int:
    # <start-full-pipeline-snippet>
    from isaacsim.asset.importer.utils import merge_mesh_utils
    from pxr import Usd

    # stage_path = "/path/to/robot.usd"
    stage = Usd.Stage.Open(stage_path)

    merge_mesh_utils.clean_mesh_operation(stage)
    merge_mesh_utils.generate_mesh_uv_normals_operation(stage)
    merged_groups = merge_mesh_utils.merge_meshes_operation(stage)

    print(f"Merged {merged_groups} rigid-body mesh group(s)")
    stage.Save()
    # <end-full-pipeline-snippet>
    return merged_groups


# -----------------------------------------------------------------------------
# Snippet: merge a hand-picked set of meshes (replaces the legacy "select prims,
# click Merge" workflow)
# -----------------------------------------------------------------------------


def snippet_explicit_merge(stage_path: str, mesh_paths: list[str]) -> None:
    # <start-explicit-merge-snippet>
    from isaacsim.asset.importer.utils import merge_mesh_utils
    from pxr import Usd

    # stage_path = "/path/to/asset.usd"
    # mesh_paths = [
    #     "/World/Jetbot/left_wheel/visual_0",
    #     "/World/Jetbot/left_wheel/visual_1",
    #     "/World/Jetbot/left_wheel/visual_2",
    # ]
    stage = Usd.Stage.Open(stage_path)

    merge_mesh_utils.merge_mesh(stage, mesh_paths)
    stage.Save()
    # <end-explicit-merge-snippet>


# -----------------------------------------------------------------------------
# Snippet: call omni.scene.optimizer.core directly
# -----------------------------------------------------------------------------


def snippet_direct_executeoperation(stage_path: str, mesh_paths: list[str]) -> None:
    # <start-direct-executeoperation-snippet>
    from omni.scene.optimizer.core import ExecutionContext, SceneOptimizerCore
    from pxr import Usd

    # stage_path = "/path/to/asset.usd"
    # mesh_paths = ["/World/A", "/World/B", "/World/C"]
    stage = Usd.Stage.Open(stage_path)

    context = ExecutionContext()
    context.set_stage(stage)
    context.generateReport = 0
    context.captureStats = 0

    core = SceneOptimizerCore.getInstance()

    core.executeOperation(
        "merge",
        context,
        {
            "meshPrimPaths": list(mesh_paths),
            "considerMaterials": True,
            "materialAlbedoAsVertexColors": False,
            "originalGeomOption": 1,
            "mergePoint": 0,
            "rootPath": mesh_paths[0],
            "considerAllAttributes": True,
            "allowSingleMeshes": False,
            "spatialMode": 0,
            "spatialThreshold": 10.0,
            "spatialMaxSize": 0.0,
            "spatialVertexCount": 10000,
            "spatialDebug": False,
        },
    )
    stage.Save()
    # <end-direct-executeoperation-snippet>


# -----------------------------------------------------------------------------
# Snippet: importer default operation configurations (reference)
# -----------------------------------------------------------------------------


def snippet_default_configs():
    # <start-default-configs-snippet>
    MESH_CLEANUP_CONFIG = {
        "paths": [],
        "mergeVertices": True,
        "tolerance": 0.0,
        "mergeBoundaries": True,
        "mergeNeighbors": True,
        "contractDegenerateEdges": True,
        "removeDegenerateFaces": True,
        "removeIsolatedVertices": True,
        "removeDuplicateFaces": True,
        "makeManifold": True,
    }

    GENERATE_NORMALS_CONFIG = {
        "paths": [],
        "binding": 0,
        "replaceExisting": True,
        "weightMode": 0,
        "sharpnessAngle": 60.0,
        "gpuThreshold": 500000,
    }

    GENERATE_PROJECTION_UVS_CONFIG = {
        "paths": [],
        "projectionType": 4,
        "useWorldSpaceScales": True,
        "scaleFactor": 0.01,
        "overwriteExisting": True,
    }

    MERGE_CONFIG = {
        "meshPrimPaths": [],
        "considerMaterials": False,
        "materialAlbedoAsVertexColors": False,
        "originalGeomOption": 1,
        "mergePoint": 0,
        "rootPath": "",
        "considerAllAttributes": True,
        "allowSingleMeshes": False,
        "spatialMode": 0,
        "spatialThreshold": 10.0,
        "spatialMaxSize": 0.0,
        "spatialVertexCount": 10000,
        "spatialDebug": True,
    }
    # <end-default-configs-snippet>
    return (
        MESH_CLEANUP_CONFIG,
        GENERATE_NORMALS_CONFIG,
        GENERATE_PROJECTION_UVS_CONFIG,
        MERGE_CONFIG,
    )


# -----------------------------------------------------------------------------
# Orchestrator and main
# -----------------------------------------------------------------------------


def _import_carter_to_temp_usd(simulation_app) -> str:
    """Import the bundled carter.urdf test asset and return the resulting USD path."""
    import omni.kit.app
    from isaacsim.asset.importer.urdf.impl import URDFImporter, URDFImporterConfig

    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_id = ext_manager.get_enabled_extension_id("isaacsim.asset.importer.urdf")
    extension_path = ext_manager.get_extension_path(ext_id)
    urdf_file = os.path.join(extension_path, "data", "urdf", "robots", "carter", "urdf", "carter.urdf")

    config = URDFImporterConfig()
    config.urdf_path = urdf_file
    config.usd_path = tempfile.mkdtemp(prefix="merge_mesh_snippet_")
    config.merge_mesh = False
    config.run_asset_transformer = False
    config.run_multi_physics_conversion = False

    importer = URDFImporter(config)
    output_usd = importer.import_urdf()
    if not output_usd:
        raise RuntimeError(f"Failed to import test URDF: {urdf_file}")
    simulation_app.update()
    return output_usd


def _collect_first_rigid_body_meshes(stage_path: str) -> list[str]:
    """Return mesh prim paths under the first rigid body that has at least two meshes."""
    from isaacsim.asset.importer.utils.impl import importer_utils
    from pxr import Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.Open(stage_path)
    for prim in stage.Traverse():
        if not (prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.HasAPI("PhysicsRigidBodyAPI")):
            continue
        meshes: list[str] = []
        prim_stack = list(prim.GetChildren())
        while prim_stack:
            child = prim_stack.pop()
            if child.HasAPI(UsdPhysics.RigidBodyAPI) or child.HasAPI("PhysicsRigidBodyAPI"):
                continue
            if child.GetTypeName() in importer_utils.USD_GEOMETRY_TYPES:
                purpose = UsdGeom.Imageable(child).GetPurposeAttr().Get()
                if purpose in (UsdGeom.Tokens.default_, UsdGeom.Tokens.render):
                    meshes.append(child.GetPath().pathString)
            prim_stack.extend(child.GetChildren())
        if len(meshes) >= 2:
            return meshes
    return []


def _run_step(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[FAILED] {name}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


def run_orchestrator(simulation_app) -> int:
    print("Snippet: default configs (reference dicts)...")
    sys.stdout.flush()
    _run_step("snippet (default configs)", snippet_default_configs)

    print("Snippet: import carter.urdf test asset...")
    sys.stdout.flush()
    stage_path = _import_carter_to_temp_usd(simulation_app)
    print(f"  Imported test stage: {stage_path}")

    print("Snippet: full importer-equivalent pipeline...")
    sys.stdout.flush()
    _run_step("snippet (full pipeline)", snippet_full_pipeline, stage_path)

    print("Snippet: explicit merge on a hand-picked mesh group...")
    sys.stdout.flush()
    second_stage = _import_carter_to_temp_usd(simulation_app)
    mesh_paths = _collect_first_rigid_body_meshes(second_stage)
    if not mesh_paths:
        print("  Skipped: no rigid body with >= 2 meshes found in test stage")
    else:
        _run_step("snippet (explicit merge)", snippet_explicit_merge, second_stage, mesh_paths)

    print("Snippet: direct Scene Optimizer executeOperation...")
    sys.stdout.flush()
    third_stage = _import_carter_to_temp_usd(simulation_app)
    mesh_paths = _collect_first_rigid_body_meshes(third_stage)
    if not mesh_paths:
        print("  Skipped: no rigid body with >= 2 meshes found in test stage")
    else:
        _run_step(
            "snippet (direct executeOperation)",
            snippet_direct_executeoperation,
            third_stage,
            mesh_paths,
        )

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run merge_mesh doc snippets.")
    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Accepted for compatibility with the doc snippet test runner; the script always runs the orchestrator.",
    )
    parser.parse_known_args()

    try:
        from isaacsim import SimulationApp

        _simulation_app = SimulationApp({"headless": True})
    except ImportError:
        print("Isaac Sim not found. Run this script with Isaac Sim's python.sh.", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    try:
        snippet_enable_scene_optimizer()

        import omni.kit.app

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_manager.set_extension_enabled_immediate("isaacsim.asset.importer.urdf", True)
        ext_manager.set_extension_enabled_immediate("isaacsim.asset.importer.utils", True)
        _simulation_app.update()

        exit_code = run_orchestrator(_simulation_app)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        exit_code = 1
    finally:
        _simulation_app.close()
    sys.exit(exit_code)
