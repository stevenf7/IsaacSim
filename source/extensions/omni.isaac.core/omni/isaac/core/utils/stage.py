import omni.kit.app
import carb
from typing import Any
from pxr import Usd, UsdGeom
import omni.kit.app
import omni


def get_current_stage():
    return omni.usd.get_context().get_stage()


# TODO: make a generic util for setting all layer properties
def set_up_axis(axis: UsdGeom.Tokens = UsdGeom.Tokens.z) -> None:
    """Change the up axis of the current stage

    Args:
        axis (UsdGeom.Tokens, optional): valid values are `UsdGeom.Tokens.y`, or `UsdGeom.Tokens.z`
    """
    from pxr import UsdGeom, Usd

    stage = get_current_stage()
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, axis)


def reset_stage() -> None:
    """
    Deletes all prims in the stage without populating the undo command buffer

    Arguments:
        stage (Usd.Stage): Stage to reset
    """

    from omni.usd.commands import DeletePrimsCommand

    stage = get_current_stage()
    # call .do() on the command directly to not populate command history
    DeletePrimsCommand(stage.Traverse()).do()


def add_usd_reference(usd_path, prim_path, type="Xform") -> Usd.Prim:
    stage = get_current_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        prim = stage.DefinePrim(prim_path, type)
    prim.GetReferences().AddReference(usd_path)
    return prim


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
