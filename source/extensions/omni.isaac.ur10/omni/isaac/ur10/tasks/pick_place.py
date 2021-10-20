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
from omni.isaac.ur10 import UR10
from omni.isaac.core.objects import DynamicCube
import numpy as np


class PickPlace(BaseTask):
    def __init__(self) -> None:
        """[summary]
        """
        self.my_ur10 = None
        self.cube = None
        self._cube_size = 0.3
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        # TODO: change values with USD
        super().set_up_scene(scene)
        self.my_ur10 = scene.add(UR10(stage=scene.stage, prim_path="/World/UR10", name="my_ur10"))
        self.my_ur10.add_gripper()
        self.cube = scene.add(
            DynamicCube(
                stage=self.scene.stage,
                name="cube_1",
                position=np.array([0.3, 0.3, self._cube_size / 2.0]) * 100,
                prim_path="/World/Cube",
                size=self._cube_size * 100,
                color=np.array([0, 0, 255]),
            )
        )
        scene.add_ground_plane(size=50.0 / self.scene.stage_units_in_meters)
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self.my_ur10.get_joints_state()
        cube_position, cube_orientation = self.cube.get_pose()
        end_effector_position, _ = self.my_ur10.get_end_effector_pose()
        # TODO: change values with USD
        return {
            "cube_1": {
                "position": cube_position,
                "orientation": cube_orientation,
                "target_position": np.array([0.7, 0.7, self._cube_size / 2.0]) * 100,
                "size": np.array([self._cube_size, self._cube_size, self._cube_size]) * 100,
            },
            "my_ur10": {"joint_positions": joints_state.positions, "end_effector_pose": end_effector_position},
        }

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        self.my_ur10.update_gripper()
        return

    def reset(self):
        return
