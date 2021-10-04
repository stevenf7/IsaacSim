# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
from typing import Any
from pxr import Usd, UsdGeom
import omni.kit.app
import omni


def set_carb_setting(carb_settings: carb.settings.ISettings, setting: str, value: Any) -> None:
    """Convenience function to set settings.

    Arguments:
        setting (str): Name of setting to change.
        value (Any): New value for the setting.

    Raises:
        TypeError: If the type of value does not match setting type.
    """
    if isinstance(value, str):
        carb_settings.set_string(setting, value)
    elif isinstance(value, bool):
        carb_settings.set_bool(setting, value)
    elif isinstance(value, int):
        carb_settings.set_int(setting, value)
    elif isinstance(value, float):
        carb_settings.set_float(setting, value)
    else:
        raise TypeError(f"Value of type {type(value)} is not supported.")


# TODO: make a generic util for setting all layer properties
def set_up_axis(stage: Usd.Stage, axis: UsdGeom.Tokens = UsdGeom.Tokens.z) -> None:
    """Change the up axis of the current stage

    Args:
        axis (UsdGeom.Tokens, optional): valid values are `UsdGeom.Tokens.y`, or `UsdGeom.Tokens.z`
    """
    from pxr import UsdGeom, Usd

    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, axis)


def reset_stage(stage: Usd.Stage) -> None:
    """
    Deletes all prims in the stage without populating the undo command buffer

    Arguments:
        stage (Usd.Stage): Stage to reset
    """

    from omni.usd.commands import DeletePrimsCommand

    # call .do() on the command directly to not populate command history
    DeletePrimsCommand(stage.Traverse()).do()


def delete_prim(prim_path):
    from omni.usd.commands import DeletePrimsCommand

    DeletePrimsCommand([prim_path]).do()


def add_usd_reference(stage, usd_path, prim_path) -> Usd.Prim:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        prim = stage.DefinePrim(prim_path, "Xform")
    prim.GetReferences().AddReference(usd_path)
    return prim


def get_extension_id(extension_name: str) -> str:
    """Get extension id for a loaded extension
        Args:
            extension_name (str): name of the extension

        Returns:
            str: Full extension id
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.get_enabled_extension_id(extension_name)


def get_extension_path(ext_id: str) -> str:
    """Get extension path for a loaded extension
        Args:
            extension_name (str): name of the extension

        Returns:
            str: Path to loaded extension root directory
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.get_extension_path(ext_id)


def enable_extension(extension_name: str) -> bool:
    """Load an extension
        Args:
            extension_name (str): name of the extension

        Returns:
            bool: True if extension could be loaded, False otherwise
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.set_extension_enabled_immediate(extension_name, True)


def set_extension_enabled(name: str, enabled: bool) -> None:
    """
    Set the state for an extension

    Args:
        name (str): name of extension to enabled
        enabled (bool): true if extension should be enabled, false to turn extension off

    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.set_extension_enabled_immediate(name, enabled)


def new_stage() -> bool:
    """
    Create a new stage
    """
    return omni.usd.get_context().new_stage()


def open_usd(usd_path: str) -> bool:
    """
    Open the given usd file and replace currently opened stage
    Args:
        usd_path (str): Path to open
    """
    if not Usd.Stage.IsSupportedFile(usd_path):
        raise ValueError("Only USD files can be loaded with this method")

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    result = omni.usd.get_context().open_stage(usd_path)
    usd_context.enable_save_to_recent_files()
    return result


def save_usd(usd_path: str) -> bool:
    """
    Save usd file to path, it will be overwritten with the current stage
    Args:
        usd_path (str): Path to save the current stage to
    """
    if not Usd.Stage.IsSupportedFile(usd_path):
        raise ValueError("Only USD files can be saved with this method")
    result = omni.usd.get_context().save_as_stage(usd_path)
    return result


def set_livesync_usd(usd_path: str, enable: bool) -> bool:
    """
    Set livesync state for a usd file

    Args:
        usd_path (str): path to enable live sync for, t will be overwritten with the current stage
        enable (bool): True to enable livesync, false to disable livesync
    """
    # TODO: Check that the provided usd_path exists
    if save_usd(usd_path):
        omni.usd.get_context().set_layer_live(usd_path, enable)
        return True
    else:
        return False
