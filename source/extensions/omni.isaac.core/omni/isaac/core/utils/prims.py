from pxr import UsdGeom, Usd
import numpy as np


def set_usd_visibility(prim, visible: bool):
    """Sets the visibility of the prim in stage. The method does this through the USD API.

    Args:
        visible (bool): flag to set the visibility of the usd prim in stage.
    """
    imageable = UsdGeom.Imageable(prim)
    if visible:
        imageable.MakeVisible()
    else:
        imageable.MakeInvisible()
    return


def create_prim(
    stage: Usd.Stage,
    stage_path: str,
    prim_type: str,
    position: np.ndarray = None,
    orientation: np.ndarray = None,
    scale: np.ndarray = None,
    usd_path: str = None,
    semantic_label: str = None,
    attributes: dict = {},
) -> Usd.Prim:
    from omni.isaac.core.utils import semantics, xforms

    prim = stage.DefinePrim(stage_path, prim_type)
    if not prim:
        return None

    for k, v in attributes.items():
        prim.GetAttribute(k).Set(v)

    if usd_path is not None:
        prim.GetReferences().AddReference(usd_path)
    if semantic_label is not None:
        semantics.add_update_semantics(prim, semantic_label)
    if position is not None:
        xforms.set_xform_position(prim, position)
    if orientation is not None:
        xforms.set_xform_orientation(prim, orientation)
    if scale is not None:
        xforms.set_xform_scale(prim, scale)
    return prim
