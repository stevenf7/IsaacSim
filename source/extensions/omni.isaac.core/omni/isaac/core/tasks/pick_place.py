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


class PickPlace(BaseTask):
    def __init__(
        self, robot, cube_initial_position=None, cube_initial_orientation=None, target_position=None, cube_size=0.0515
    ) -> None:
        """[summary]
        """
        BaseTask.__init__(self, name="pick_place")
        self._robot = robot
        self._target_cube = None
        self._cube_initial_position = cube_initial_position
        self._cube_initial_orientation = cube_initial_orientation
        self._target_position = target_position
        self._cube_size = cube_size
        if self._cube_initial_position is None:
            self._cube_initial_position = np.array([0.3, 0.3, 0.3])
        if self._cube_initial_orientation is None:
            self._cube_initial_orientation = np.array([0, 0, 0, 1])
        if self._target_position is None:
            self._target_position = np.array([-0.3, -0.3, self._cube_size / 2.0])
        return

    def get_robot(self):
        return self._robot

    def get_target_cube(self):
        return self._target_cube

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        scene.add_ground_plane()
        scene.add(self._robot)

        self.cube = scene.add(
            DynamicCube(
                name="cube_1",
                position=self._cube_initial_position,
                orientation=self._cube_initial_orientation,
                prim_path="/World/Cube",
                size=self._cube_size,
                color=np.array([0, 0, 1]),
            )
        )
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self._robot.get_joints_state()
        cube_position, cube_orientation = self.cube.get_world_pose()
        end_effector_position, _ = self._robot.end_effector.get_world_pose()
        return {
            "cube_1": {
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
        self._robot.gripper.set_positions(self._robot.gripper.open_position)
        return
