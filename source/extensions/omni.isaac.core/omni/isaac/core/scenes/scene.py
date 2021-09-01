# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.scenes.scene_registry import SceneRegistry
from omni.isaac.core.objects.ground_plane import GroundPlane
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.robots.robot import Robot
import omni.usd.commands
from pxr import Usd


class Scene(object):
    def __init__(self, stage: Usd.Stage) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
        """
        self._scene_registry = SceneRegistry()
        self._stage = stage

    @property
    def stage(self) -> Usd.Stage:
        """[summary]

        Returns:
            Usd.Stage: [description]
        """
        return self._stage

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
        if isinstance(obj, RigidPrim):
            self._scene_registry.add_rigid_object(name=obj.name, rigid_object=obj)
        elif isinstance(obj, GeometryPrim):
            self._scene_registry.add_visual_object(name=obj.name, visual_object=obj)
        elif isinstance(obj, Articulation):
            self._scene_registry.add_articulated_system(name=obj.name, articulated_system=obj)
        elif isinstance(obj, Robot):
            self._scene_registry.add_robot(name=obj.name, robot=obj)
        else:
            raise Exception("object type is not supported yet")
        return obj

    def add_ground_plane(
        self, size: float = 50, z_position: float = 0, prim_path: str = "/World/groundPlane", thickness: float = 0.5
    ) -> None:
        """[summary]

        Args:
            size (float, optional): [description]. Defaults to 50.
            z_position (float, optional): [description]. Defaults to 0.
            prim_path (str, optional): [description]. Defaults to "/World/groundPlane".
            thickness (float, optional): [description]. Defaults to 0.5.
        """
        GroundPlane(
            stage=self.stage,
            prim_path=prim_path,
            name="ground_plane",
            z_position=z_position,
            size=size,
            thickness=thickness,
        )
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
        return self._scene_registry.get_object(name=name)

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
        return

    def check_collisions(self) -> bool:
        """[summary]

        Raises:
            NotImplementedError: [description]

        Returns:
            bool: [description]
        """
        raise NotImplementedError

    def get_contacts(self, object_one, object_two):
        """[summary]

        Args:
            object_one ([type]): [description]
            object_two ([type]): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def check_scene_realistic(self) -> bool:
        """[summary]

        Raises:
            NotImplementedError: [description]

        Returns:
            bool: [description]
        """
        raise NotImplementedError
