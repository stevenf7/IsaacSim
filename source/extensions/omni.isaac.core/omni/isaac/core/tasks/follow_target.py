# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.objects import DynamicCube, VisualCube
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.prims import is_prim_path_valid
import numpy as np
from collections import OrderedDict


class FollowTarget(BaseTask):
    def __init__(
        self,
        robot,
        target_prim_path="/World/TargetCube",
        target_name="target",
        target_position=None,
        target_orientation=None,
    ) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name="follow_target")
        self._robot = robot
        self._target_name = target_name
        self._target = None
        self._target_prim_path = target_prim_path
        self._target_position = target_position
        self._target_orientation = target_orientation
        self._target_visual_material = None
        self._obstacle_cubes = OrderedDict()
        return

    def get_robot(self):
        return self._robot

    def get_target(self):
        return self._target

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        scene.add_ground_plane()
        scene.add(self._robot)
        if self._target_position is None:
            self._target_position = np.array([0, 0.1, 0.7])

        if self._target_orientation is None:
            self._target_orientation = np.array([0, 0, 0, 1])
        self.set_target(
            prim_path=self._target_prim_path,
            position=self._target_position,
            orientation=self._target_orientation,
            target_name=self._target_name,
        )
        return

    def set_target(self, prim_path, position=None, orientation=None, target_name="target"):
        # if target exists delete it from scene
        if self._target is not None:
            print("delete it from scene")
        else:
            if is_prim_path_valid(prim_path):
                self._target = self.scene.add(
                    XFormPrim(prim_path=prim_path, position=position, orientation=orientation, name=target_name)
                )
            else:
                self._target = self.scene.add(
                    VisualCube(
                        name=target_name,
                        prim_path=prim_path,
                        position=position,
                        orientation=orientation,
                        color=np.array([1, 0, 0]),
                        size=0.03,
                    )
                )
            self._target_visual_material = self._target.get_applied_visual_material()
            if self._target_visual_material is not None:
                if hasattr(self._target_visual_material, "set_color"):
                    self._target_visual_material.set_color(np.array([1, 0, 0]))
        return

    def set_target_world_pose(self, position, orientation):
        if self._target is None:
            raise Exception("You need to define a target before setting its world pose")
        self._target.set_world_pose(position=position, orientation=orientation)
        return

    def set_target_local_pose(self, position, orientation):
        if self._target is None:
            raise Exception("You need to define a target before setting its world pose")
        self._target.set_local_pose(position=position, orientation=orientation)
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self._robot.get_joints_state()
        target_position, _ = self._target.get_world_pose()
        return {
            self._robot.name: {
                "joint_positions": np.array(joints_state.positions),
                "joint_velocities": np.array(joints_state.velocities),
            },
            self._target.name: {"position": np.array(target_position)},
        }

    def target_reached(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        end_effector_position, _ = self._robot.end_effector.get_world_pose()
        target_position, _ = self._target.get_world_pose()
        if np.mean(np.abs(np.array(end_effector_position) - np.array(target_position))) < 0.025:
            return True
        else:
            return False

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        if self._target_visual_material is not None:
            if hasattr(self._target_visual_material, "set_color"):
                if self.target_reached():
                    self._target_visual_material.set_color(color=np.array([0, 1.0, 0]))
                else:
                    self._target_visual_material.set_color(color=np.array([1.0, 0, 0]))

        return

    def reset(self) -> None:
        """[summary]
        """
        return

    def add_obstacle(self, position: np.ndarray = np.array([0.1, 0.1, 1.0])):
        """[summary]

        Args:
            position (np.ndarray, optional): [description]. Defaults to np.array([0.1, 0.1, 1.0]).
        """
        cube = self.scene.add(
            DynamicCube(
                name="cube_" + str(len(self._obstacle_cubes)),
                position=position,
                prim_path="/World/ObstacleCube_" + str(len(self._obstacle_cubes)),
                size=0.1,
                color=np.array([0, 0, 1.0]),
            )
        )
        self._obstacle_cubes[cube.name] = cube
        return cube

    def remove_obstacle(self, name: Optional[str] = None) -> None:
        """[summary]

        Args:
            name (Optional[str], optional): [description]. Defaults to None.
        """
        if name is not None:
            self.scene.remove_object(name)
            del self._obstacle_cubes[name]
        else:
            obstacle_to_delete = list(self._obstacle_cubes.keys())[-1]
            self.scene.remove_object(obstacle_to_delete)
            del self._obstacle_cubes[obstacle_to_delete]
        return

    def get_obstacle_to_delete(self):
        obstacle_to_delete = list(self._obstacle_cubes.keys())[-1]
        return self.scene.get_object(obstacle_to_delete)

    def obstacles_exist(self) -> bool:
        if len(self._obstacle_cubes) > 0:
            return True
        else:
            return False

    def cleanup(self) -> None:
        obstacles_to_delete = list(self._obstacle_cubes.keys())
        for obstacle_to_delete in obstacles_to_delete:
            self.scene.remove_object(obstacle_to_delete)
            del self._obstacle_cubes[obstacle_to_delete]
        return
