# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.scenes.scene_registry import SceneRegistry
from omni.isaac.core.objects.ground_plane import GroundPlane
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.robots.robot import Robot
from omni.isaac.core.utils.prims import get_prim_parent, get_prim_path, is_prim_root_path, is_prim_ancestral
import omni.usd.commands
from pxr import Usd, UsdGeom
import numpy as np
import builtins
from omni.isaac.core.utils.stage import get_current_stage, update_stage_async, update_stage
import asyncio
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.stage import add_reference_to_stage
import gc


class Scene(object):
    def __init__(self) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
        """
        self._scene_registry = SceneRegistry()
        self._enable_bounding_box_computations = False
        self._bbox_cache = None
        return

    @property
    def stage(self) -> Usd.Stage:
        """[summary]

        Returns:
            Usd.Stage: [description]
        """
        return get_current_stage()

    def add(self, obj: XFormPrim) -> XFormPrim:
        """[summary]

        Args:
            obj (XFormPrim): [description]
            name (str): [description]

        Raises:
            Exception: [description]

        Returns:
            XFormPrim: [description]
        """
        if self._scene_registry.name_exists(obj.name):
            raise Exception("Cannot add the object {} to the scene since its name is not unique".format(obj.name))
        if isinstance(obj, RigidPrim):
            self._scene_registry.add_rigid_object(name=obj.name, rigid_object=obj)
        elif isinstance(obj, GeometryPrim):
            self._scene_registry.add_geometry_object(name=obj.name, geometry_object=obj)
        elif isinstance(obj, Robot):
            self._scene_registry.add_robot(name=obj.name, robot=obj)
        elif isinstance(obj, Articulation):
            self._scene_registry.add_articulated_system(name=obj.name, articulated_system=obj)
        elif isinstance(obj, XFormPrim):
            self._scene_registry.add_xform(name=obj.name, xform=obj)
        else:
            raise Exception("object type is not supported yet")
        return obj

    def add_ground_plane(
        self,
        size: float = None,
        z_position: float = 0,
        name="ground_plane",
        prim_path: str = "/World/groundPlane",
        static_friction=0.5,
        dynamic_friction=0.5,
        restitution=0.8,
        color: np.ndarray = None,
    ) -> None:
        """[summary]

        Args:
            size (float, optional): [description]. Defaults to 50.
            z_position (float, optional): [description]. Defaults to 0.
            prim_path (str, optional): [description]. Defaults to "/World/groundPlane".
            thickness (float, optional): [description]. Defaults to 0.5.
        """
        if Scene.object_exists(self, name=name):
            carb.log_info("ground floor already created with name {}.".format(name))
            return Scene.get_object(self, name=name)
        plane = GroundPlane(
            prim_path=prim_path,
            name=name,
            z_position=z_position,
            size=size,
            color=color,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
        )
        Scene.add(self, plane)
        return plane

    def add_default_ground_plane(
        self,
        size: float = None,
        z_position: float = 0,
        name="default_ground_plane",
        prim_path: str = "/World/defaultGroundPlane",
        static_friction=0.5,
        dynamic_friction=0.5,
        restitution=0.8,
    ):
        if Scene.object_exists(self, name=name):
            carb.log_info("ground floor already created with name {}.".format(name))
            return Scene.get_object(self, name=name)
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
        usd_path = nucleus_server + "/Isaac/Environments/Grid/default_environment.usd"
        add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
        plane = GroundPlane(
            prim_path=prim_path,
            name=name,
            size=size,
            z_position=z_position,
            static_friction=static_friction,
            dynamic_friction=dynamic_friction,
            restitution=restitution,
        )
        Scene.add(self, plane)
        return plane

    def post_reset(self) -> None:
        """[summary]
        """
        prim_registries_available = [
            self._scene_registry._prim_objects,
            self._scene_registry._geometry_objects,
            self._scene_registry._rigid_objects,
            self._scene_registry._articulated_systems,
            self._scene_registry._robots,
            self._scene_registry.xforms,
        ]

        for prim_registery in prim_registries_available:
            for prim_name in list(prim_registery):
                if not prim_registery[prim_name].is_valid():
                    prim_object = prim_registery[prim_name]
                    self._scene_registry.remove_object(name=prim_name)
                    del prim_object
                else:
                    prim_registery[prim_name].post_reset()
        if self._enable_bounding_box_computations:
            self._bbox_cache.Clear()
        gc.collect()
        return

    def _finalize(self) -> None:
        """[summary]
        """
        for articulation_name, articulated_system in self._scene_registry.articulated_systems.items():
            articulated_system.initialize()
        for robot_name, robot in self._scene_registry.robots.items():
            robot.initialize()
        for rigid_object_name, rigid_object in self._scene_registry.rigid_objects.items():
            rigid_object.initialize()
        return

    def remove_object(self, name: str = None, prim_path: str = None) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        prim_object = self.get_object(name=name, prim_path=prim_path)
        # sometimes the prim path is under a reference
        current_prim = prim_object.prim
        prim_path = get_prim_path(current_prim)
        while not is_prim_root_path(prim_path):
            if not is_prim_ancestral(prim_path):
                break
            current_prim = get_prim_parent(current_prim)
            prim_path = get_prim_path(current_prim)
        omni.usd.commands.DeletePrimsCommand([get_prim_path(current_prim)]).do()
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            update_stage()
        self._scene_registry.remove_object(name=name, prim_path=prim_path)
        del prim_object
        return

    def get_object(self, name: str = None, prim_path: str = None) -> XFormPrim:
        """[summary]

        Args:
            name (str): [description]

        Returns:
            XFormPrim: [description]
        """
        return self._scene_registry.get_object(name=name, prim_path=prim_path)

    def object_exists(self, name: str) -> bool:
        """[summary]

        Args:
            name (str): [description]

        Returns:
            XFormPrim: [description]
        """
        if self._scene_registry.name_exists(name):
            return True
        else:
            return False

    def clear(self) -> None:
        """[summary]
        """
        for prim_name in list(self._scene_registry._prim_objects):
            self.remove_object(prim_name)
        for geometry_object_name in list(self._scene_registry._geometry_objects):
            self.remove_object(geometry_object_name)
        for rigid_object_name in list(self._scene_registry._rigid_objects):
            self.remove_object(rigid_object_name)
        for articulated_system_name in list(self._scene_registry._articulated_systems):
            self.remove_object(articulated_system_name)
        for robot_name in list(self._scene_registry._robots):
            self.remove_object(robot_name)
        for xform_name in list(self._scene_registry.xforms):
            self.remove_object(xform_name)
        return

    def compute_object_AABB(self, name: str):
        if not self._enable_bounding_box_computations:
            raise Exception("bounding box computations should be enabled before quering AABB of an object")
        bounds = self._bbox_cache.ComputeWorldBound(self.get_object(name).prim)
        prim_range = bounds.ComputeAlignedRange()
        return np.array([np.array(prim_range.GetMin()), np.array(prim_range.GetMax())])

    def enable_bounding_boxes_computations(self):
        self._bbox_cache = UsdGeom.BBoxCache(
            time=Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_], useExtentsHint=False
        )
        self._enable_bounding_box_computations = True
        return

    def disable_bounding_boxes_computations(self):
        self._bbox_cache = None
        self._enable_bounding_box_computations = False
        return
