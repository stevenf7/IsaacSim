# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from abc import abstractmethod
from omni.isaac.core.articulations import ArticulationGripper
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.objects import DynamicCube
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.string import find_unique_string_name
import numpy as np


class PickPlace(BaseTask):
    def __init__(
        self,
        name,
        cube_initial_position=None,
        cube_initial_orientation=None,
        target_position=None,
        cube_size=None,
        task_frame_translation=None,
    ) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name=name)
        self._robot = None
        self._target_cube = None
        self._cube = None
        self._cube_initial_position = cube_initial_position
        self._cube_initial_orientation = cube_initial_orientation
        self._target_position = target_position
        self._cube_size = cube_size
        if self._cube_size is None:
            self._cube_size = 0.0515 / get_stage_units()
        self._task_frame_translation = task_frame_translation
        if self._cube_initial_position is None:
            self._cube_initial_position = np.array([0.3, 0.3, 0.3]) / get_stage_units()
        if self._cube_initial_orientation is None:
            self._cube_initial_orientation = np.array([0, 0, 0, 1])
        if self._target_position is None:
            self._target_position = np.array([-0.3, -0.3, 0]) / get_stage_units()
            self._target_position[2] = self._cube_size / 2.0
        if self._task_frame_translation is None:
            self._task_frame_translation = np.array([0.0, 0.0, 0.0])
        self._target_position = self._target_position + self._task_frame_translation
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        scene.add_ground_plane(size=50.0 / get_stage_units())
        cube_prim_path = find_unique_string_name(
            intitial_name="/World/Cube", is_unique_fn=lambda x: not is_prim_path_valid(x)
        )
        cube_name = find_unique_string_name(
            intitial_name="cube", is_unique_fn=lambda x: not self.scene.object_exists(x)
        )
        self._cube = scene.add(
            DynamicCube(
                name=cube_name,
                position=self._cube_initial_position + self._task_frame_translation,
                orientation=self._cube_initial_orientation,
                prim_path=cube_prim_path,
                size=self._cube_size,
                color=np.array([0, 0, 1]),
            )
        )
        self._task_objects[self._cube.name] = self._cube
        self._robot = self.set_robot()
        scene.add(self._robot)
        position, orientation = self._robot.get_world_pose()
        self._robot.set_world_pose(position=position + self._task_frame_translation, orientation=orientation)
        self._robot.set_default_state(position=position + self._task_frame_translation, orientation=orientation)
        self._task_objects[self._robot.name] = self._robot
        return

    @abstractmethod
    def set_robot(self):
        raise NotImplementedError

    def set_params(self, cube_position=None, cube_orientation=None, target_position=None):
        if target_position is not None:
            self._target_position = target_position
        if cube_position is not None or cube_orientation is not None:
            self._cube.set_world_pose(position=cube_position, orientation=cube_orientation)
        return

    def get_params(self):
        params_representation = dict()
        position, orientation = self._cube.get_world_pose()
        params_representation["cube_position"] = {"value": position, "modifiable": True}
        params_representation["cube_orientation"] = {"value": orientation, "modifiable": True}
        params_representation["target_position"] = {"value": self._target_position, "modifiable": True}
        params_representation["cube_name"] = {"value": self._cube.name, "modifiable": False}
        params_representation["robot_name"] = {"value": self._robot.name, "modifiable": False}
        return params_representation

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self._robot.get_joints_state()
        cube_position, cube_orientation = self._cube.get_world_pose()
        end_effector_position, _ = self._robot.end_effector.get_world_pose()
        return {
            self._cube.name: {
                "position": cube_position,
                "orientation": cube_orientation,
                "target_position": self._target_position,
            },
            self._robot.name: {
                "joint_positions": joints_state.positions,
                "end_effector_position": end_effector_position,
            },
        }

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def reset(self):
        if isinstance(self._robot.gripper, ArticulationGripper):
            self._robot.gripper.set_positions(self._robot.gripper.open_position)
        return
