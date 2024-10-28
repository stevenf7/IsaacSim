# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.

# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.kit.app
import omni.kit.commands
from pxr import Sdf, Usd


def create_exposed_variable(
    prim: Usd.Prim, full_attr_name: str, attr_type: Sdf.ValueTypeName, default_value, doc: str = None
) -> Usd.Attribute:
    """Creates a USD attribute on the prim to expose variables in the UI."""
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        carb.log_warn(f"Attribute {full_attr_name} already exists on {prim.GetPath()} with value {attr.Get()}")
        return attr
    attr = prim.CreateAttribute(full_attr_name, attr_type)
    attr.Set(default_value)
    if doc:
        attr.SetDocumentation(doc)
    return attr


def create_exposed_variables(prim: Usd.Prim, exposed_attr_ns: str, behavior_ns: str, variables_to_expose: dict) -> None:
    """Create exposed variables based on the provided namespaces and data dictionary"""
    # Check if there are any attributes to lock (e.g. constant placeholders -- cannot be edited in the UI)
    attr_to_lock = []
    for var in variables_to_expose:
        attr_name = var["attr_name"]
        full_attr_name = f"{exposed_attr_ns}:{behavior_ns}:{attr_name}"
        attr = create_exposed_variable(
            prim=prim,
            full_attr_name=full_attr_name,
            attr_type=var["attr_type"],
            default_value=var["default_value"],
            doc=var.get("doc"),
        )
        if var.get("lock"):
            attr_to_lock.append(attr.GetPath())
    import asyncio

    asyncio.ensure_future(lock_exposed_variables(attr_to_lock))


async def lock_exposed_variables(attr_paths):
    """Lock exposed variables to prevent editing in the UI."""
    await omni.kit.app.get_app().next_update_async()
    omni.kit.commands.execute("LockSpecsCommand", spec_paths=attr_paths)


def check_if_exposed_variables_should_be_removed(prim: Usd.Prim, script_file_path: str) -> bool:
    """Exposed variables should be removed if the script is no longer assigned to the prim (not in list)."""
    if not prim.IsValid():
        return False

    scripts_attr = prim.GetAttribute("omni:scripting:scripts")
    if not scripts_attr:
        return True

    scripts_paths: Sdf.AssetPathArray = scripts_attr.Get()
    is_script_in_list = any(script_file_path == asset.path for asset in scripts_paths)

    # Return True if the script_file_path is not in the list of scripts
    return not is_script_in_list


def remove_exposed_variable(prim: Usd.Prim, full_attr_name: str) -> None:
    """Remove the exposed variable from the prim."""
    if not prim.IsValid():
        carb.log_warn(f"Prim {prim.GetPath()} is not valid, cannot remove exposed variable {full_attr_name}")
        return
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        prim.RemoveProperty(attr.GetName())
    else:
        carb.log_warn(f"Attribute {full_attr_name} not found on {prim.GetPath()}")


def remove_exposed_variables(prim: Usd.Prim, exposed_attr_ns: str, behavior_ns: str, variables_to_expose: dict) -> None:
    """Remove exposed variables based on the provided namespaces and data dictionary"""
    for var in variables_to_expose:
        attr_name = var["attr_name"]
        full_attr_name = f"{exposed_attr_ns}:{behavior_ns}:{attr_name}"
        remove_exposed_variable(prim, full_attr_name)


def get_exposed_variable(prim: Usd.Prim, full_attr_name: str):
    """Helper function to get the value of an exposed attribute."""
    attr = prim.GetAttribute(full_attr_name)
    if attr:
        return attr.Get()
    else:
        return None


def remove_empty_scopes(prim: Usd.Prim, stage: Usd.Stage) -> None:
    """Recursively (post-order) remove Scope or GenericPrim prims with no valid children from stage."""
    for child in prim.GetChildren():
        remove_empty_scopes(child, stage)

    prim_type = prim.GetTypeName() or "GenericPrim"

    if prim_type in ("GenericPrim", "Scope"):
        if not any(child.IsValid() for child in prim.GetChildren()):
            stage.RemovePrim(prim.GetPath())
