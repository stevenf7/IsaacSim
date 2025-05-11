# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from isaacsim import SimulationApp

# The most basic usage for creating a simulation app
kit = SimulationApp(launch_config={"disable_viewport_updates": True})

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


def check_stage_units(stage, usd_path):
    units = UsdGeom.GetStageMetersPerUnit(stage)
    if units != 1.0:
        return [f"stage: {usd_path}, has stage which are not in meters"]
    else:
        return []


def check_physics_schema(usd_path):
    if get_physx_interface().check_backwards_compatibility() is True:
        return [f"stage: {usd_path}, has an old physics schema"]
    else:
        return []


def check_missing_ref(usd_path, prim):
    if prim_has_missing_references(prim) is True:
        return [f"stage: {usd_path}, has missing references for {prim}"]
    else:
        return []


def check_external_refs(root_path, usd_path):
    ext_refs = [i for i in get_stage_references(usd_path, resolve_relatives=False) if is_path_external(i, root_path)]
    if len(ext_refs) != 0:
        return [f"stage: {usd_path}, has external references {ext_refs}"]
    else:
        return []


def check_abs_refs(usd_path):
    abs_refs = [i for i in get_stage_references(usd_path) if is_absolute_path(i)]
    if len(abs_refs) != 0:
        return [f"stage: {usd_path}, has absolute references {abs_refs}"]
    else:
        return []


def check_properties(item, prim):
    abs_refs = []
    try:
        if prim.GetAttributes() is not None:
            for attr in prim.GetAttributes():
                if attr.GetTypeName() == Sdf.ValueTypeNames.String:
                    if attr.Get() is not None:
                        if "omniverse://" in attr.Get():
                            abs_refs.append(attr.Get())

        if len(abs_refs) != 0:
            return [f"File:{item} Prim {prim} Contains a absolute reference {abs_refs}"]
        return []
    except Exception as e:
        carb.log_error(f"{e} fail to check {item}, {prim}")


def check_deleted_ref(usd_path, prim):
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
    return []


def check_deprecated_og(usd_path, prim):
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return []
    if prim.HasAttribute("node:type"):
        type_attr = prim.GetAttribute("node:type")
        value = type_attr.Get()
        if "omni.graph.nodes.MakeArray" in value:
            return [f"stage: {usd_path}, has node {prim.GetPath()} of type omni.graph.nodes.MakeArray"]
    return []


for i in range(10):
    kit.update()

root_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/default")
search_path = [
    root_path + "/Isaac",
]
exclude_path = ["Environments/Outdoor/Rivermark", ".thumbs"]

all_files = find_files_recursive(search_path)
sub_files = [file for file in all_files if is_valid_usd_file(file, exclude_path)]
print(f"found a total of {len(all_files)} files and {len(sub_files)} usd* files")

total_files = len(sub_files)
results = []
for item in sub_files:
    print(f"opening: {item}")
    file_results = []
    # first make sure all assets open
    kit.update()

    open_stage(item)
    kit.update()
    while is_stage_loading():
        kit.update()
    stage = get_current_stage()
    for prim in stage.Traverse():
        file_results.extend(check_missing_ref(item, prim))
        file_results.extend(check_deleted_ref(item, prim))
        file_results.extend(check_deleted_payload(item, prim))
        file_results.extend(check_properties(item, prim))
        file_results.extend(check_physics_scene(item, prim))
        file_results.extend(check_deprecated_og(item, prim))
    file_results.extend(check_stage_units(stage, item))
    file_results.extend(check_abs_refs(item))
    file_results.extend(check_external_refs(root_path, item))
    results.extend(file_results)
if len(results) > 0:
    for l in results:
        carb.log_error(l)

kit.close()  # Cleanup application
