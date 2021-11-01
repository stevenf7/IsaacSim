# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from abc import abstractmethod
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.articulations import ArticulationGripper
import numpy as np
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.string import find_unique_string_name


class Stacking(BaseTask):
    def __init__(
        self,
        name,
        cube_initial_positions,
        cube_initial_orientations=None,
        stack_target_position=None,
        cube_size=None,
        offset=None,
    ) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name=name, offset=offset)
        self._robot = None
        self._num_of_cubes = cube_initial_positions.shape[0]
        self._cube_initial_positions = cube_initial_positions
        self._cube_initial_orientations = cube_initial_orientations
        self._offset = offset
        if self._cube_initial_orientations is None:
            self._cube_initial_orientations = [None] * self._num_of_cubes
        self._stack_target_position = stack_target_position
        self._cube_size = cube_size
        if self._cube_size is None:
            self._cube_size = np.array([0.0515, 0.0515, 0.0515]) / get_stage_units()
        if self._offset is None:
            self._offset = np.array([0.0, 0.0, 0.0])
        if stack_target_position is None:
            self._stack_target_position = np.array([-0.3, -0.3, 0]) / get_stage_units()
        self._stack_target_position = self._stack_target_position + self._offset
        self._cubes = []
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        scene.add_ground_plane()
        for i in range(self._num_of_cubes):
            color = np.random.uniform(size=(3,))
            cube_prim_path = find_unique_string_name(
                intitial_name="/World/Cube", is_unique_fn=lambda x: not is_prim_path_valid(x)
            )
            cube_name = find_unique_string_name(
                intitial_name="cube", is_unique_fn=lambda x: not self.scene.object_exists(x)
            )
            self._cubes.append(
                scene.add(
                    DynamicCuboid(
                        name=cube_name,
                        position=self._cube_initial_positions[i] + self._offset,
                        orientation=self._cube_initial_orientations[i],
                        prim_path=cube_prim_path,
                        size=self._cube_size,
                        color=color,
                    )
                )
            )
            self._task_objects[self._cubes[-1].name] = self._cubes[-1]
        self._robot = self.set_robot()
        scene.add(self._robot)
        position, orientation = self._robot.get_world_pose()
        self._robot.set_world_pose(position=position + self._offset, orientation=orientation)
        self._robot.set_default_state(position=position + self._offset, orientation=orientation)
        self._task_objects[self._robot.name] = self._robot
        return

    @abstractmethod
    def set_robot(self):
        raise NotImplementedError

    def set_params(self, cube_name=None, cube_position=None, cube_orientation=None, stack_target_position=None):
        if stack_target_position is not None:
            self._stack_target_position = stack_target_position
        if cube_name is not None:
            self._task_objects[cube_name].set_world_pose(position=cube_position, orientation=cube_orientation)
        return

    def get_params(self):
        params_representation = dict()
        params_representation["stack_target_position"] = {"value": self._stack_target_position, "modifiable": True}
        params_representation["robot_name"] = {"value": self._robot.name, "modifiable": False}
        return params_representation

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self._robot.get_joints_state()
        end_effector_position, _ = self._robot.end_effector.get_world_pose()
        observations = {
            self._robot.name: {
                "joint_positions": joints_state.positions,
                "end_effector_position": end_effector_position,
            }
        }
        for i in range(self._num_of_cubes):
            cube_position, cube_orientation = self._cubes[i].get_world_pose()
            observations[self._cubes[i].name] = {
                "position": cube_position,
                "orientation": cube_orientation,
                "target_position": np.array(
                    [
                        self._stack_target_position[0],
                        self._stack_target_position[1],
                        (self._cube_size[2] * i) + self._cube_size[2] / 2.0,
                    ]
                ),
            }
        return observations

    def pre_step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def post_reset(self):
        if isinstance(self._robot.gripper, ArticulationGripper):
            self._robot.gripper.set_positions(self._robot.gripper.open_position)
        return

    def get_cube_names(self):
        cube_names = []
        for i in range(self._num_of_cubes):
            cube_names.append(self._cubes[i].name)
        return cube_names

    def get_robot_name(self):
        return self._robot.name

    @abstractmethod
    def calculate_metrics(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    @abstractmethod
    def is_done(self) -> None:
        """[summary]
        """
        raise NotImplementedError
