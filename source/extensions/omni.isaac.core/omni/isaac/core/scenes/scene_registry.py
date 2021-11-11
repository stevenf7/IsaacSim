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
from typing import Optional


class SceneRegistry(object):
    def __init__(self) -> None:
        """[summary]
        """
        self._prim_objects = dict()
        self._rigid_objects = dict()
        self._geometry_objects = dict()
        self._articulated_systems = dict()
        self._robots = dict()
        self._xforms = dict()
        self._prim_path_to_object = dict()
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
        self._prim_path_to_object[rigid_object.prim_path] = rigid_object
        return

    def add_articulated_system(self, name, articulated_system: Articulation) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            articulated_system (Articulation): [description]
        """
        self._articulated_systems[name] = articulated_system
        self._prim_path_to_object[articulated_system.prim_path] = articulated_system
        return

    def add_geometry_object(self, name, geometry_object: GeometryPrim) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            geometry_object (GeometryPrim): [description]
        """
        self._geometry_objects[name] = geometry_object
        self._prim_path_to_object[geometry_object.prim_path] = geometry_object
        return

    def add_robot(self, name, robot: Robot) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            robot (Robot): [description]
        """
        self._robots[name] = robot
        self._prim_path_to_object[robot.prim_path] = robot
        return

    def add_xform(self, name, xform: XFormPrim) -> None:
        """[summary]

        Args:
            name ([type]): [description]
            robot (Robot): [description]
        """
        self._xforms[name] = xform
        self._prim_path_to_object[xform.prim_path] = xform
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
            or name in self._geometry_objects
            or name in self._xforms
        ):
            return True
        else:
            return False

    def prim_path_exists(self, prim_path: str) -> bool:
        """[summary]

        Args:
            prim_path (str): [description]

        Returns:
            bool: [description]
        """
        if prim_path in self._prim_path_to_object:
            return True
        else:
            return False

    def remove_object(self, name: Optional[str] = None, prim_path: Optional[str] = None) -> None:
        """[summary]

        Args:
            name (Optional[str], optional): [description]. Defaults to None.
            prim_path (Optional[str], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
            Exception: [description]
            NotImplementedError: [description]
            Exception: [description]
        """
        if name is None and prim_path is None:
            raise Exception("name or prim_path should be specified to remove the object accordingly")
        if name is not None:
            if name in self._robots:
                del self._prim_path_to_object[self._robots[name].prim_path]
                del self._robots[name]
                return
            elif name in self._articulated_systems:
                del self._prim_path_to_object[self._articulated_systems[name].prim_path]
                del self._articulated_systems[name]
                return
            elif name in self._rigid_objects:
                del self._prim_path_to_object[self._rigid_objects[name].prim_path]
                del self._rigid_objects[name]
                return
            elif name in self._geometry_objects:
                del self._prim_path_to_object[self._geometry_objects[name].prim_path]
                del self._geometry_objects[name]
                return
            elif name in self._xforms:
                del self._prim_path_to_object[self._xforms[name].prim_path]
                del self._xforms[name]
                return
            else:
                raise Exception("Cannot remove object {} from the scene since it doesn't exist".format(name))
        if prim_path is not None:
            if prim_path in self._prim_path_to_object:
                name = self._prim_path_to_object[prim_path].name
                del self._prim_path_to_object[prim_path]
                if name in self._robots:
                    del self._robots[name]
                    return
                elif name in self._articulated_systems:
                    del self._articulated_systems[name]
                    return
                elif name in self._rigid_objects:
                    del self._rigid_objects[name]
                    return
                elif name in self._geometry_objects:
                    del self._geometry_objects[name]
                    return
                elif name in self._xforms:
                    del self._xforms[name]
                    return
                else:
                    raise NotImplementedError
            else:
                raise Exception(
                    "Cannot remove object with prim_path {} from the scene since it doesn't exist".format(prim_path)
                )

    def get_object(self, name: Optional[str] = None, prim_path: Optional[str] = None) -> XFormPrim:
        """[summary]

        Args:
            name (Optional[str], optional): [description]. Defaults to None.
            prim_path (Optional[str], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]

        Returns:
            XFormPrim: [description]
        """
        if name is None and prim_path is None:
            raise Exception("name or prim_path should be specified to get the object accordingly")
        if name is not None:
            if name in self._robots:
                return self._robots[name]
            elif name in self._articulated_systems:
                return self._articulated_systems[name]
            elif name in self._rigid_objects:
                return self._rigid_objects[name]
            elif name in self._geometry_objects:
                return self._geometry_objects[name]
            elif name in self._xforms:
                return self._xforms[name]
        if prim_path is not None:
            return self._prim_path_to_object[prim_path]
