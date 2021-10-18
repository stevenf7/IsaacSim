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
import omni.usd.commands
from pxr import Usd, UsdGeom
import numpy as np
from omni.isaac.core.utils.stage import get_current_stage


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
            self._scene_registry.add_visual_object(name=obj.name, visual_object=obj)
        elif isinstance(obj, Articulation):
            self._scene_registry.add_articulated_system(name=obj.name, articulated_system=obj)
        elif isinstance(obj, Robot):
            self._scene_registry.add_robot(name=obj.name, robot=obj)
        elif isinstance(obj, XFormPrim):
            self._scene_registry.add_xform(name=obj.name, xform=obj)
        else:
            raise Exception("object type is not supported yet")
        return obj

    def add_ground_plane(
        self, size: float = 50, z_position: float = 0, prim_path: str = "/World/groundPlane", color: np.ndarray = None
    ) -> None:
        """[summary]

        Args:
            size (float, optional): [description]. Defaults to 50.
            z_position (float, optional): [description]. Defaults to 0.
            prim_path (str, optional): [description]. Defaults to "/World/groundPlane".
            thickness (float, optional): [description]. Defaults to 0.5.
        """
        GroundPlane(prim_path=prim_path, name="ground_plane", z_position=z_position, size=size, color=color)
        # TODO: add it to the registery?
        return

    def reset(self) -> None:
        """[summary]
        """
        for prim_name, prim in self._scene_registry._prim_objects.items():
            prim.reset()
        for visual_object_name, visual_object in self._scene_registry._visual_objects.items():
            visual_object.reset()
        for rigid_object_name, rigid_object in self._scene_registry._rigid_objects.items():
            rigid_object.reset()
        for articulated_system_name, articulated_system in self._scene_registry._articulated_systems.items():
            articulated_system.reset()
        for robot_name, robot in self._scene_registry._robots.items():
            robot.reset()
        for xform_name, xform in self._scene_registry.xforms.items():
            xform.reset()
        if self._enable_bounding_box_computations:
            self._bbox_cache.Clear()
        return

    def _finalize(self) -> None:
        """[summary]
        """
        for articulation_name, articulated_system in self._scene_registry.articulated_systems.items():
            articulated_system._initialize_handles()
        for robot_name, robot in self._scene_registry.robots.items():
            robot._initialize_handles()
        for rigid_object_name, rigid_object in self._scene_registry.rigid_objects.items():
            rigid_object._initialize_handles()
        return

    def remove_object(self, name: str) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        if not self._scene_registry.name_exists(name):
            raise Exception("Cannot remove object {} from the scene since it doesn't exist".format(name))
        prim_object = self.get_object(name=name)
        omni.usd.commands.DeletePrimsCommand([prim_object.prim_path]).do()
        self._scene_registry.remove_object(name=name)
        del prim_object
        return

    def get_object(self, name: str) -> XFormPrim:
        """[summary]

        Args:
            name (str): [description]

        Returns:
            XFormPrim: [description]
        """
        if not self._scene_registry.name_exists(name):
            raise Exception("Cannot get object {} from the scene since it doesn't exist".format(name))
        return self._scene_registry.get_object(name=name)

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

    def clear_scene(self) -> None:
        """[summary]
        """
        for prim_name, prim in self._scene_registry._prim_objects.items():
            self.remove_object(prim_name)
        for visual_object_name, visual_object in self._scene_registry._visual_objects.items():
            self.remove_object(visual_object_name)
        for rigid_object_name, rigid_object in self._scene_registry._rigid_objects.items():
            self.remove_object(rigid_object_name)
        for articulated_system_name, articulated_system in self._scene_registry._articulated_systems.items():
            self.remove_object(articulated_system_name)
        for robot_name, robot in self._scene_registry._robots.items():
            self.remove_object(robot_name)
        for xform_name, xform in self._scene_registry.xforms.items():
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
