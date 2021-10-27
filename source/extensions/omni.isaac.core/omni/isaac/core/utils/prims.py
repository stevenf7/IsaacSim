from omni import usd
from pxr import UsdGeom, Usd
import numpy as np
from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from omni.isaac.dynamic_control import _dynamic_control


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


def get_prim_at_descendent_path(prim_path, filterfn=None):
    prim = get_current_stage().GetPrimAtPath(prim_path)
    childrenStack = [prim]
    out = prim.GetChildren()
    while len(childrenStack) > 0:
        prim = childrenStack.pop(0)
        if filterfn(get_prim_path(prim)):
            return get_prim_path(prim)
        children = prim.GetChildren()
        childrenStack = childrenStack + children
        out = out + children
    return None


def get_prim_children(prim):
    return prim.GetChildren()


def get_prim_parent(prim):
    return prim.GetParent()


def query_parent_path(prim_path, query_fn):
    current_prim_path = get_prim_path(get_prim_parent(get_prim_at_path(prim_path)))
    while not is_prim_root_path(current_prim_path):
        if query_fn(current_prim_path):
            return True
        current_prim_path = get_prim_path(get_prim_parent(get_prim_at_path(current_prim_path)))
    return False


def is_prim_root_path(prim_path):
    if "/" == prim_path or get_prim_path(get_prim_parent(get_prim_at_path(prim_path))) == prim_path:
        return True
    else:
        return False


def get_prim_path(prim):
    return prim.GetPath().pathString


def set_prim_visibility(prim, visible: bool):
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
    prim_path: str,
    prim_type: str,
    position: np.ndarray = None,
    translation: np.ndarray = None,
    orientation: np.ndarray = None,
    scale: np.ndarray = None,
    usd_path: str = None,
    semantic_label: str = None,
    attributes: dict = {},
) -> Usd.Prim:
    from omni.isaac.core.utils import semantics
    from omni.isaac.core.prims import XFormPrim

    prim = define_prim(prim_path=prim_path, prim_type=prim_type)
    if not prim:
        return None

    for k, v in attributes.items():
        prim.GetAttribute(k).Set(v)

    if usd_path is not None:
        add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
    if semantic_label is not None:
        semantics.add_update_semantics(prim, semantic_label)
    XFormPrim(prim_path=prim_path, position=position, translation=translation, orientation=orientation, scale=scale)
    return prim


def delete_prim(prim_path):
    from omni.usd.commands import DeletePrimsCommand

    DeletePrimsCommand([prim_path]).do()


def get_prim_property(prim_path, property_name):
    prim = get_prim_at_path(prim_path=prim_path)
    return prim.GetAttribute(property_name).Get()


def set_prim_property(prim_path, property_name, property_value):
    prim = get_prim_at_path(prim_path=prim_path)
    prim.GetAttribute(property_name).Set(property_value)
    return


def get_prim_object_type(prim_path):
    dc_interface = _dynamic_control.acquire_dynamic_control_interface()
    object_type = dc_interface.peek_object_type(prim_path)
    if object_type == _dynamic_control.OBJECT_NONE:
        prim = get_prim_at_path(prim_path)
        if prim.IsA(UsdGeom.Xformable):
            return "xform"
        else:
            return None
    elif object_type == _dynamic_control.OBJECT_RIGIDBODY:
        return "rigid_body"
    elif object_type == _dynamic_control.OBJECT_JOINT:
        return "joint"
    elif object_type == _dynamic_control.OBJECT_DOF:
        return "dof"
    elif object_type == _dynamic_control.OBJECT_ARTICULATION:
        return "articulation"
    elif object_type == _dynamic_control.OBJECT_ATTRACTOR:
        return "attractor"
    elif object_type == _dynamic_control.OBJECT_D6JOINT:
        return "d6joint"
    else:
        raise Exception("the object type is not support here yet")
