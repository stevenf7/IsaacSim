# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" Cortex-specific utilities and helper methods
"""

import numpy as np

from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid, DynamicCuboid
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.prims import (
    get_prim_at_path,
    get_prim_path,
    get_prim_children,
    define_prim,
    is_prim_path_valid,
)
from omni.isaac.core.utils.stage import get_stage_units, add_reference_to_stage
from omni.isaac.core.utils.types import JointsState, ArticulationAction
from omni.isaac.franka import Franka
from omni.isaac.universal_robots import UR10
from omni.isaac.motion_generation import MotionPolicyController, ArticulationMotionPolicy, RmpFlowSmoothed
import omni.isaac.motion_generation.interface_config_loader as icl
from pxr import Sdf, Gf, UsdPhysics, UsdGeom, Usd
from pxr.Vt import Bool, Double

from omni.isaac.cortex.motion_commander import MotionCommander
from omni.isaac.cortex.math_util import to_stage_units

import carb


def load_behavior_module(behavior_filepath, module_name="behavior"):
    from importlib.machinery import SourceFileLoader

    return SourceFileLoader(module_name, behavior_filepath).load_module()


def get_assets_root_path_or_die():
    """ Find the assets root path and check for errors.

    Raises a runtime error if the assets root could not be found. Otherwise, returns the asset
    root path.
    """
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        err_str = "Could not find Isaac Sim assets folder"
        carb.log_error(err_str)
        raise RuntimeError(err_str)
    return assets_root_path


def is_a_rigid_prim(prim):
    """ Returns True if the prim is a rigid prim.

    A prim is designated as a rigid prim if it has a rigid body API and a mass API.
    """
    return prim.HasAPI(UsdPhysics.RigidBodyAPI) and prim.HasAPI(UsdPhysics.MassAPI)


def make_core_object_from_prim(prim_path, name):
    """ Create a core object from the USD at the specified prim path.

    If the prim at the prim path is a cube, then it returns a DynamicCuboid wraping the prim if
    it's also a rigid prim, or a FixedCuboid if it's not.

    If the prim is not a cube, then simply wraps it in a generic XFormPrim object.

    Note that to add an object to the motion commander as an obstacle, it needs to be a core API
    object type. This method currently only supports wrapping UsdGeom.Cube USD types this way, so
    only cubes can be obstacles.
    """
    prim = get_prim_at_path(prim_path)
    if prim.IsA(UsdGeom.Cube):
        if is_a_rigid_prim(prim):
            return DynamicCuboid(prim_path=prim_path, name=name)
        else:
            return FixedCuboid(prim_path=prim_path, name=name)
    return XFormPrim(prim_path=prim_path, name=name)


def make_core_objects(domain="belief", additional_paths={}, verbose=False):
    """ Creates an objects dict mapping object name to XFormPrim wrapping existing xform prims in
    the stage.
    
    Looks up a collection of objects at the specified stage path and creates XFormPrim wrappers for
    them. Adds them to an objects dict mapping the name (under the objects_path) to the XFormPrim
    object. Creates XFormPrim objects for each path specified in the additional_paths dict as well,
    using the key from that dict as the key for the new objects dict. Returns the resulting objects
    dict.
    """

    objects_path = "/cortex/%s/objects" % domain

    objects = {}
    obstacles = {}
    if is_prim_path_valid(objects_path):
        if verbose:
            print("core objs path is valid:", objects_path)
        objects_prim = get_prim_at_path(objects_path)
        prim_children = get_prim_children(objects_prim)
        for prim in prim_children:
            prim_path = get_prim_path(prim)
            if prim_path.endswith("/properties"):
                continue

            name = prim_path[len(objects_path + "/") :]
            if domain != "belief":
                name = domain + "_" + name
            print("adding object:", name)
            objects[name] = make_core_object_from_prim(prim_path=prim_path, name=name)

            is_obs_attr = "cortex:is_obstacle"
            if prim.HasAttribute(is_obs_attr) and prim.GetAttribute(is_obs_attr).Get():
                print("Adding object prim as obstacle:", prim_path)
                obstacles[name] = objects[name]
    else:
        print("core objs path is invalid:", objects_path)

    for name, path in additional_paths.items():
        objects[name] = make_core_object_from_prim(prim_path=path, name=name)

    return objects, obstacles
