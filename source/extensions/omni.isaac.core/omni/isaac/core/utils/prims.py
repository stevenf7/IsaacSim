from pxr import UsdGeom, Usd
import numpy as np
from omni.isaac.core.utils.stage import get_current_stage


def get_prim_at_path(prim_path):
    return get_current_stage().GetPrimAtPath(prim_path)


def is_prim_path_valid(prim_path):
    return get_current_stage().GetPrimAtPath(prim_path).IsValid()


def define_prim(prim_path, prim_type="Xform"):
    if is_prim_path_valid(prim_path):
        raise Exception("A prim already exists at prim path: {}".format(prim_path))
    return get_current_stage().DefinePrim(prim_path, prim_type)


def get_prim_type_name(prim_path):
    if not is_prim_path_valid(prim_path):
        raise Exception("A prim does not exist at prim path: {}".format(prim_path))
    prim = get_prim_at_path(prim_path)
    return prim.GetPrimTypeInfo().GetTypeName()


def traverse_prim_path(prim_path, filterfn=None):
    prim = get_current_stage().GetPrimAtPath(prim_path)
    childrenStack = [prim]
    out = prim.GetChildren()
    while len(childrenStack) > 0:
        prim = childrenStack.pop(0)
        if not filterfn or (filterfn and filterfn(prim)):
            children = prim.GetChildren()
            childrenStack = childrenStack + children
            out = out + children
    return out


def get_prim_children(prim):
    return prim.GetChildren()


def get_prim_parent(prim):
    return prim.GetParent()


def get_prim_path(prim):
    return prim.GetPath().pathString


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
