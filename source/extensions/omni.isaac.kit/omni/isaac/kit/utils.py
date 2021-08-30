# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
from typing import Optional, Any
from pxr import Usd, UsdGeom


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
def set_up_axis(stage: Usd.Stage, axis: Optional(UsdGeom.Tokens) = UsdGeom.Tokens.z) -> None:
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
