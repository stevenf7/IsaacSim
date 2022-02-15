# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from pxr import UsdGeom, Usd
import numpy as np
from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from omni.isaac.dynamic_control import _dynamic_control
import omni.kit
import omni.usd
import typing


def get_prim_at_path(prim_path: str) -> Usd.Prim:
    """Get the USD Prim at a given path string

    Args:
        prim_path (str): path of the prim in the stage

    Returns:
        Usd.Prim: USD Prim object at the given path in the current stage
    """
    return get_current_stage().GetPrimAtPath(prim_path)


def is_prim_path_valid(prim_path: str) -> bool:
    """Check if a path has a valid USD Prim at it

    Args:
        prim_path (str): path of the prim in the stage

    Returns:
        bool: True if the path points to a valid prim
    """
    return get_current_stage().GetPrimAtPath(prim_path).IsValid()


def define_prim(prim_path: str, prim_type: str = "Xform") -> Usd.Prim:
    """Create a USD Prim at the given prim_path of type prim_type unless one already exists

    Args:
        prim_path (str): path of the prim in the stage
        prim_type (str, optional): The type of the prim to create. Defaults to "Xform".

    Raises:
        Exception: If there is already a prim at the prim_path

    Returns:
        Usd.Prim: Creates a USD Prim at the prim_path of type prim_type
    """
    if is_prim_path_valid(prim_path):
        raise Exception("A prim already exists at prim path: {}".format(prim_path))
    return get_current_stage().DefinePrim(prim_path, prim_type)


def get_prim_type_name(prim_path: str) -> str:
    """Get the TypeName of the USD Prim at the path if it is valid

    Args:
        prim_path (str): path of the prim in the stage

    Raises:
        Exception: If there is not a valid prim at the given path

    Returns:
        str: The TypeName of the USD Prim at the path string
    """
    if not is_prim_path_valid(prim_path):
        raise Exception("A prim does not exist at prim path: {}".format(prim_path))
    prim = get_prim_at_path(prim_path)
    return prim.GetPrimTypeInfo().GetTypeName()


def move_prim(path_from: str, path_to: str) -> None:
    """Run the Move command to change a prims USD Path in the stage

    Args:
        path_from (str): Path of the USD Prim you wish to move
        path_to (str): Final destination of the prim
    """
    from omni.usd.commands import MovePrimCommand

    MovePrimCommand(path_from=path_from, path_to=path_to).do()
    return


def get_first_matching_child_prim(prim_path: str, predicate: typing.Callable[[str], bool]) -> str:
    """Recursively get the first USD Prim at the path string that passes the predicate function

    Args:
        prim_path (str): path of the prim in the stage
        predicate (typing.Callable[[str], bool]): Function to test the prims against

    Returns:
        str: Returns the first prim or child of the prim, as defined by GetChildren, that passes the predicate
    """
    prim = get_current_stage().GetPrimAtPath(prim_path)
    children_stack = [prim]
    out = prim.GetChildren()
    while len(children_stack) > 0:
        prim = children_stack.pop(0)
        if predicate(get_prim_path(prim)):
            return get_prim_path(prim)
        children = prim.GetChildren()
        children_stack = children_stack + children
        out = out + children
    return None


def get_all_matching_child_prims(
    prim_path: str, predicate: typing.Callable[[str], bool] = lambda x: True
) -> typing.List[str]:
    """Get the USD Prim and all it's children that pass the predicate

    Args:
        prim_path (str): path of the prim in the stage
        predicate (typing.Callable[[str], bool]): Function to test prim against.  False tests will be ignored.  Defaults to always True.

    Returns:
        typing.List[str]: A List of the given prim and all its children that pass the predicate, even children under prims that don't pass.
    """
    prim = get_prim_at_path(prim_path)
    traversal_queue = [prim]
    out = []
    while len(traversal_queue) > 0:
        prim = traversal_queue.pop(0)
        if predicate(get_prim_path(prim)):
            out.append(get_prim_path(prim))
        children = get_prim_children(prim)
        traversal_queue = traversal_queue + children
    return out


def get_prim_children(prim: Usd.Prim) -> typing.List[Usd.Prim]:
    """Return the call of the USD Prim's GetChildren member function

    Args:
        prim (Usd.Prim): The USD Prim to call GetChildren on

    Returns:
        typing.List[Usd.Prim]: A list of the prim's children returnd by GetChildren
    """
    return prim.GetChildren()


def get_prim_parent(prim: Usd.Prim) -> Usd.Prim:
    """Return the call of the USD Prim's GetChildren member function

    Args:
        prim (Usd.Prim): The USD Prim to call GetParent on

    Returns:
        Usd.Prim: The prim's parent returned from GetParent
    """
    return prim.GetParent()


def query_parent_path(prim_path: str, predicate: typing.Callable[[str], bool]) -> bool:
    """Check if one of the ancestros of the prim at the prim_path can pass the predicate

    Args:
        prim_path (str): path to the USD Prim with whome to check the ancestors of
        predicate (typing.Callable[[str], bool]): The condition that must be True about the ancestors

    Returns:
        bool: True if there is an ancestor that can pass the predicate, False otherwise
    """
    current_prim_path = get_prim_path(get_prim_parent(get_prim_at_path(prim_path)))
    while not is_prim_root_path(current_prim_path):
        if predicate(current_prim_path):
            return True
        current_prim_path = get_prim_path(get_prim_parent(get_prim_at_path(current_prim_path)))
    return False


def is_prim_ancestral(prim_path: str) -> bool:
    """Check if any of the prims ancestors were brought in as a reference
        Returns:
            True if prim is part of a referenced prim, false otherwise"""
    return omni.usd.check_ancestral(get_prim_at_path(prim_path))


def is_prim_root_path(prim_path: str) -> bool:
    """Returns:
            True if the prim path is "/", False otherwise
    """
    if prim_path == "/":
        return True
    else:
        return False


def is_prim_no_delete(prim_path: str) -> bool:
    """Returns:
            True if prim cannot be deleted, False if it can
    """
    return get_prim_at_path(prim_path).GetMetadata("no_delete")


def is_prim_hidden_in_stage(prim_path: str) -> bool:
    """Returns:
            True if prim is hidden from stage window, False if not hidden
            This is not related to the prim visibility
    """
    return get_prim_at_path(prim_path).GetMetadata("hide_in_stage_window")


def get_prim_path(prim: Usd.Prim) -> str:
    return prim.GetPath().pathString


def set_prim_visibility(prim: Usd.Prim, visible: bool) -> None:
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
    prim_type: str = "Xform",
    position: typing.Optional[np.ndarray] = None,
    translation: typing.Optional[np.ndarray] = None,
    orientation: typing.Optional[np.ndarray] = None,
    scale: typing.Optional[np.ndarray] = None,
    usd_path: typing.Optional[str] = None,
    semantic_label: typing.Optional[str] = None,
    semantic_type: str = "class",
    attributes: typing.Optional[dict] = None,
) -> Usd.Prim:
    """Create a prim, apply specified transforms, apply semantic label and
    set specified attributes.

    args:
        prim_path (str): The path of the new prim.
        prim_type (str): Prim type name
        position (np.ndarray (3), optional): prim position (applied last)
        translation (np.ndarray (3), optional): prim translation (applied last)
        orientation (np.ndarray (4), optional): prim rotation as quaternion
        scale (np.ndarray (3), optional): scaling factor in x, y, z.
        usd_path (str, optional): Path to the USD that this prim will reference.
        semantic_label (str, optional): Semantic label.
        semantic_type (str, optional): set to "class" unless otherwise specified.
        attributes (dict, optional): Key-value pairs of prim attributes to set.
    """

    from omni.isaac.core.utils import semantics
    from omni.isaac.core.prims import XFormPrim

    prim = define_prim(prim_path=prim_path, prim_type=prim_type)
    if not prim:
        return None

    if attributes is None:
        attributes = {}

    for k, v in attributes.items():
        prim.GetAttribute(k).Set(v)

    if usd_path is not None:
        add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
    if semantic_label is not None:
        semantics.add_update_semantics(prim, semantic_label, semantic_type)
    XFormPrim(prim_path=prim_path, position=position, translation=translation, orientation=orientation, scale=scale)
    return prim


def delete_prim(prim_path: str) -> None:
    """Remove the USD Prim and its decendants from the scene if able

    Args:
        prim_path (str): path of the prim in the stage
    """
    from omni.usd.commands import DeletePrimsCommand

    DeletePrimsCommand([prim_path]).do()
    return


def get_prim_property(prim_path: str, property_name: str) -> typing.Any:
    """Get the attribute of the USD Prim at the given path

    Args:
        prim_path (str): path of the prim in the stage
        property_name (str): name of the attribute to get

    Returns:
        typing.Any: The attribute if it exists, None otherwise
    """
    prim = get_prim_at_path(prim_path=prim_path)
    return prim.GetAttribute(property_name).Get()


def set_prim_property(prim_path: str, property_name: str, property_value: typing.Any) -> None:
    """Set the attribute of the USD Prim at the path

    Args:
        prim_path (str): path of the prim in the stage
        property_name (str): name of the attribute to set
        property_value (typing.Any): value to set the attribute to
    """
    prim = get_prim_at_path(prim_path=prim_path)
    prim.GetAttribute(property_name).Set(property_value)
    return


def get_prim_object_type(prim_path: str) -> str:
    """Get the Dynamic Control Object Type, e.g. rigid_body, joint, of the USD Prim at the given path

    Args:
        prim_path (str): path of the prim in the stage

    Raises:
        Exception: If the USD Prim is not a suppored type.

    Returns:
        str: returns the dynamic control type--i.e. rigid_body, joint, dof, articulation, attractor, d6joint--if there is one,  "xform" for Xformatble prims, and None otherwise.
    """
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
