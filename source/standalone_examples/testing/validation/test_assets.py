# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Asset validation test script that checks USD assets for common issues."""

import csv

# Standard library imports
import os

# Initialize simulation app first
from isaacsim import SimulationApp

kit = SimulationApp(launch_config={"disable_viewport_updates": True})

# Isaac Sim imports
import carb
import omni
from isaacsim.core.utils.stage import get_current_stage, is_stage_loading, open_stage
from isaacsim.storage.native import (
    find_files_recursive,
    get_stage_references,
    is_absolute_path,
    is_path_external,
    is_valid_usd_file,
    prim_has_missing_references,
)
from omni.physx import get_physx_interface
from pxr import PhysxSchema, Sdf, UsdGeom

# Configuration
RESULTS_FILE = "asset_validation_results.txt"
CSV_RESULTS_FILE = "asset_validation_results.csv"


def check_stage_units(stage, usd_path):
    """Check if stage units are in meters.

    Args:
        stage: The USD stage to check.
        usd_path: Path to the USD file.

    Returns:
        List of error messages if stage units are not in meters.
    """
    units = UsdGeom.GetStageMetersPerUnit(stage)
    if units != 1.0:
        return [f"stage: {usd_path}, has stage which are not in meters"]
    return []


def check_physics_schema(usd_path):
    """Check if physics schema is up to date.

    Args:
        usd_path: Path to the USD file.

    Returns:
        List of error messages if physics schema is outdated.
    """
    if get_physx_interface().check_backwards_compatibility() is True:
        return [f"stage: {usd_path}, has an old physics schema"]
    return []


def check_missing_ref(usd_path, prim):
    """Check if prim has missing references.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if prim has missing references.
    """
    if prim_has_missing_references(prim) is True:
        return [f"stage: {usd_path}, has missing references for {prim}"]
    return []


def check_external_refs(root_path, usd_path):
    """Check if USD file has external references.

    Args:
        root_path: Root path for asset validation.
        usd_path: Path to the USD file.

    Returns:
        List of error messages if USD file has external references.
    """
    ext_refs = [i for i in get_stage_references(usd_path, resolve_relatives=False) if is_path_external(i, root_path)]
    if len(ext_refs) != 0:
        return [f"stage: {usd_path}, has external references {ext_refs}"]
    return []


def check_abs_refs(usd_path):
    """Check if USD file has absolute references.

    Args:
        usd_path: Path to the USD file.

    Returns:
        List of error messages if USD file has absolute references.
    """
    abs_refs = [i for i in get_stage_references(usd_path) if is_absolute_path(i)]
    if len(abs_refs) != 0:
        return [f"stage: {usd_path}, has absolute references {abs_refs}"]
    return []


def check_properties(usd_path, prim):
    """Check if prim properties contain absolute references.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if prim properties contain absolute references.
    """
    abs_refs = []
    try:
        if prim.GetAttributes() is not None:
            for attr in prim.GetAttributes():
                if attr.GetTypeName() == Sdf.ValueTypeNames.String:
                    if attr.Get() is not None:
                        if "omniverse://" in attr.Get():
                            abs_refs.append(attr.Get())

        if len(abs_refs) != 0:
            return [f"File:{usd_path} Prim {prim} Contains a absolute reference {abs_refs}"]
        return []
    except Exception as e:
        carb.log_error(f"{e} fail to check {usd_path}, {prim}")
        return []


def check_deleted_ref(usd_path, prim):
    """Check if prim has deleted references.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if prim has deleted references.
    """
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return []
    ref_prim_spec = stage.GetRootLayer().GetPrimAtPath(prim.GetPath())
    if ref_prim_spec:
        references_info = ref_prim_spec.GetInfo("references")
        if len(references_info.deletedItems) > 0:
            return [f"stage: {usd_path}, has deleted references {references_info.deletedItems}"]
    return []


def check_deleted_payload(usd_path, prim):
    """Check if prim has deleted payloads.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if prim has deleted payloads.
    """
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return []
    ref_prim_spec = stage.GetRootLayer().GetPrimAtPath(prim.GetPath())
    if ref_prim_spec:
        payload_info = ref_prim_spec.GetInfo("payload")
        if len(payload_info.deletedItems) > 0:
            return [f"stage: {usd_path}, has deleted payload {payload_info.deletedItems}"]
    return []


def check_physics_scene(usd_path, prim):
    """Check if physics scene has valid configuration.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if physics scene has invalid configuration.
    """
    errors = []
    if prim.HasAPI(PhysxSchema.PhysxSceneAPI):
        physics_api = PhysxSchema.PhysxSceneAPI(prim)
        if physics_api.GetEnableGPUDynamicsAttr().Get():
            errors.append(f"Physics scene: {prim} in {usd_path}, has gpu dynamics enabled")
        if physics_api.GetBroadphaseTypeAttr().Get() != "MBP":
            errors.append(
                f"Physics scene: {prim} in {usd_path}, has {physics_api.GetBroadphaseTypeAttr().Get()} broadphase"
            )
    return errors


def check_deprecated_og(usd_path, prim):
    """Check if prim uses deprecated Omniverse Graph nodes.

    Args:
        usd_path: Path to the USD file.
        prim: The USD prim to check.

    Returns:
        List of error messages if prim uses deprecated Omniverse Graph nodes.
    """
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return []
    if prim.HasAttribute("node:type"):
        type_attr = prim.GetAttribute("node:type")
        value = type_attr.Get()
        if "omni.graph.nodes.MakeArray" in value:
            return [f"stage: {usd_path}, has node {prim.GetPath()} of type omni.graph.nodes.MakeArray"]
    return []


def validate_usd_file(usd_path, root_path):
    """Validate a single USD file against all validation checks.

    Args:
        usd_path: Path to the USD file to validate.
        root_path: Root path for asset validation.

    Returns:
        List of validation errors found.
    """
    file_results = []

    # Open stage and wait until loaded
    open_stage(usd_path)
    kit.update()
    while is_stage_loading():
        kit.update()

    stage = get_current_stage()
    if not stage:
        return [f"Failed to open stage: {usd_path}"]

    # Check stage-level issues
    # file_results.extend(check_stage_units(stage, usd_path))
    file_results.extend(check_abs_refs(usd_path))
    file_results.extend(check_external_refs(root_path, usd_path))

    # Check prim-level issues
    for prim in stage.Traverse():
        file_results.extend(check_missing_ref(usd_path, prim))
        file_results.extend(check_deleted_ref(usd_path, prim))
        file_results.extend(check_deleted_payload(usd_path, prim))
        file_results.extend(check_properties(usd_path, prim))
        file_results.extend(check_physics_scene(usd_path, prim))
        file_results.extend(check_deprecated_og(usd_path, prim))

    return file_results


# Wait for simulator to initialize
for i in range(10):
    kit.update()

# Main validation process
try:
    # Setup paths and filters
    root_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/default")
    search_paths = [
        root_path + "/Isaac",
    ]
    exclude_paths = ["Environments/Outdoor/Rivermark", ".thumbs"]

    # Find all USD files to validate
    all_files = find_files_recursive(search_paths)
    usd_files = [file for file in all_files if is_valid_usd_file(file, exclude_paths)]
    print(f"Found a total of {len(all_files)} files and {len(usd_files)} USD files")

    # Create/clear results file
    with open(RESULTS_FILE, "w") as f:
        f.write(f"USD Asset Validation Results\n")
        f.write(f"==========================\n\n")

    # Create/clear CSV results file
    with open(CSV_RESULTS_FILE, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["USD File", "Error"])

    # Process each USD file and collect validation results
    all_errors = []
    total_files = len(usd_files)

    with open(RESULTS_FILE, "a") as results_file, open(CSV_RESULTS_FILE, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)

        for i, usd_path in enumerate(usd_files):
            print(f"[{i+1}/{total_files}] Validating: {usd_path}")

            # Validate the file
            file_errors = validate_usd_file(usd_path, root_path)

            # Write errors to results file immediately
            if file_errors:
                results_file.write(f"\n--- {usd_path} ---\n")
                for error in file_errors:
                    results_file.write(f"  • {error}\n")
                    # Write to CSV file
                    csv_writer.writerow([usd_path, error])

            # Add to overall results
            all_errors.extend(file_errors)

    # Report overall validation results
    print(f"\nValidation complete. Found {len(all_errors)} errors.")
    print(f"Results saved to: {RESULTS_FILE} and {CSV_RESULTS_FILE}")

    # Log all errors to console
    if all_errors:
        for error in all_errors:
            carb.log_error(error)

finally:
    # Ensure clean application shutdown
    kit.close()
