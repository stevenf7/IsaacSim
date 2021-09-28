# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.robots.robot import Robot


class SceneRegistry(object):
    def __init__(self) -> None:
        """[summary]
        """
        self._prim_objects = dict()
        self._rigid_objects = dict()
        self._visual_objects = dict()
        self._articulated_systems = dict()
        self._robots = dict()
        self._xforms = dict()
        return

    @property
    def articulated_systems(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return self._articulated_systems

    @property
    def rigid_objects(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return self._rigid_objects

    @property
    def robots(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return self._robots

    @property
    def xforms(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return self._xforms

    # TODO: add if name exists check uniqueness
    def add_rigid_object(self, name, rigid_object: RigidPrim) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            rigid_object (RigidPrim): [description]
        """
        self._rigid_objects[name] = rigid_object
        return

    def add_articulated_system(self, name, articulated_system: Articulation) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            articulated_system (Articulation): [description]
        """
        self._articulated_systems[name] = articulated_system
        return

    def add_visual_object(self, name, visual_object: GeometryPrim) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            visual_object (GeometryPrim): [description]
        """
        self._visual_objects[name] = visual_object
        return

    def add_robot(self, name, robot: Robot) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            robot (Robot): [description]
        """
        self._robots[name] = robot
        return

    def add_xform(self, name, xform: XFormPrim) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            robot (Robot): [description]
        """
        self._xforms[name] = xform
        return

    def name_exists(self, name: str) -> bool:
        """[summary]

        Args:
            name (str): [description]

        Returns:
            bool: [description]
        """
        if (
            name in self._robots
            or name in self._articulated_systems
            or name in self._rigid_objects
            or name in self._visual_objects
            or name in self._xforms
        ):
            return True
        else:
            return False

    def remove_object(self, name: str) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        if name in self._robots:
            del self._robots[name]
        elif name in self._articulated_systems:
            del self._articulated_systems[name]
        elif name in self._rigid_objects:
            del self._rigid_objects[name]
        elif name in self._visual_objects:
            del self._visual_objects[name]
        elif name in self._xforms:
            del self._xforms[name]
        return

    def get_object(self, name: str) -> XFormPrim:
        """[summary]

        Args:
            name (str): [description]

        Returns:
            XFormPrim: [description]
        """
        if name in self._robots:
            return self._robots[name]
        elif name in self._articulated_systems:
            return self._articulated_systems[name]
        elif name in self._rigid_objects:
            return self._rigid_objects[name]
        elif name in self._visual_objects:
            return self._visual_objects[name]
        elif name in self._xforms:
            return self._xforms[name]
