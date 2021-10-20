# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.objects import DynamicCube
import numpy as np


class Stacking(BaseTask):
    def __init__(
        self,
        robot,
        cube_initial_positions,
        cube_initial_orientations=None,
        stack_target_position=None,
        cube_size=0.0515,
    ) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name="stacking")
        self._robot = robot
        self._num_of_cubes = cube_initial_positions.shape[0]
        self._cube_initial_positions = cube_initial_positions
        self._cube_initial_orientations = cube_initial_orientations
        if self._cube_initial_orientations is None:
            self._cube_initial_orientations = [None] * self._num_of_cubes
        self._stack_target_position = stack_target_position
        self._cube_size = cube_size
        if stack_target_position is None:
            self._stack_target_position = np.array([-0.3, -0.3, 0])
        self._cubes = []
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        scene.add_ground_plane()
        scene.add(self._robot)
        for i in range(self._num_of_cubes):
            color = np.random.uniform(size=(3,))
            self._cubes.append(
                scene.add(
                    DynamicCube(
                        name="cube_" + str(i),
                        position=self._cube_initial_positions[i],
                        orientation=self._cube_initial_orientations[i],
                        prim_path="/World/Cube" + str(i),
                        size=self._cube_size,
                        color=color,
                    )
                )
            )
        return

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
                        (self._cube_size * i) + self._cube_size / 2.0,
                    ]
                ),
            }
        return observations

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def reset(self):
        self._robot.gripper.set_positions(self._robot.gripper.open_position)
        return

    def get_cube_names(self):
        cube_names = []
        for i in range(self._num_of_cubes):
            cube_names.append(self._cubes[i].name)
        return cube_names

    def get_robot_name(self):
        return self._robot.name
