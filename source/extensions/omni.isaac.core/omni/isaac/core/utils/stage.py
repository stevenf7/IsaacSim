import omni.kit.app
from pxr import Usd, UsdGeom
from omni.isaac.core.utils.constants import AXES_TOKEN
import builtins


def get_current_stage():
    return omni.usd.get_context().get_stage()


# TODO: make a generic util for setting all layer properties
def set_stage_up_axis(axis: str = "z") -> None:
    """Change the up axis of the current stage

    Args:
        axis (UsdGeom.Tokens, optional): valid values are "x" and "y"
    """
    stage = get_current_stage()
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, AXES_TOKEN[axis])
    return


def clear_stage(keep_physics=True) -> None:
    """
    Deletes all prims in the stage without populating the undo command buffer

    Arguments:
        stage (Usd.Stage): Stage to reset
    """

    from omni.usd.commands import DeletePrimsCommand
    from omni.isaac.core.utils.prims import get_prim_path, get_prim_type_name

    if keep_physics:
        paths = []
        for prim in traverse_stage():
            prim_path = get_prim_path(prim)
            if get_prim_type_name(prim_path=prim_path) == "PhysicsScene":
                continue
            paths.append(prim.GetPrimPath())
        DeletePrimsCommand(paths).do()
    else:
        stage = get_current_stage()
        # call .do() on the command directly to not populate command history
        DeletePrimsCommand(stage.Traverse()).do()
    if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
        omni.kit.app.get_app_interface().update()
    return


def add_reference_to_stage(usd_path, prim_path, type="Xform") -> Usd.Prim:
    stage = get_current_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        prim = stage.DefinePrim(prim_path, type)
    prim.GetReferences().AddReference(usd_path)
    return prim


def create_new_stage() -> bool:
    """
    Create a new stage
    """
    return omni.usd.get_context().new_stage()


async def create_new_stage_async() -> Usd.Stage:
    await omni.usd.get_context().new_stage_async()
    await omni.kit.app.get_app().next_update_async()
    return


def open_stage(usd_path: str) -> bool:
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


def save_stage(usd_path: str) -> bool:
    """
    Save usd file to path, it will be overwritten with the current stage
    Args:
        usd_path (str): Path to save the current stage to
    """
    if not Usd.Stage.IsSupportedFile(usd_path):
        raise ValueError("Only USD files can be saved with this method")
    result = omni.usd.get_context().save_as_stage(usd_path)
    return result


def close_stage(callback_fn=None) -> bool:
    if callback_fn is None:
        result = omni.usd.get_context().close_stage()
    else:
        result = omni.usd.get_context().close_stage_with_callback(callback_fn)
    return result


def set_livesync_stage(usd_path: str, enable: bool) -> bool:
    """
    Set livesync state for a usd file

    Args:
        usd_path (str): path to enable live sync for, t will be overwritten with the current stage
        enable (bool): True to enable livesync, false to disable livesync
    """
    # TODO: Check that the provided usd_path exists
    if save_stage(usd_path):
        omni.usd.get_context().set_layer_live(usd_path, enable)
        return True
    else:
        return False


def traverse_stage():
    return get_current_stage().Traverse()


def is_stage_loading() -> bool:
    """
        bool: Convenience function to see if any files are being loaded. True if loading, False otherwise
    """
    context = omni.usd.get_context()
    if context is None:
        return False
    else:
        _, _, loading = context.get_stage_loading_status()
        return loading > 0


def set_stage_units(stage_units_in_meters):
    if get_current_stage() is None:
        raise Exception("There is no stage currently opened, init_stage needed before calling this func")
    UsdGeom.SetStageMetersPerUnit(get_current_stage(), stage_units_in_meters)
    return


def get_stage_units():
    return UsdGeom.GetStageMetersPerUnit(get_current_stage())
