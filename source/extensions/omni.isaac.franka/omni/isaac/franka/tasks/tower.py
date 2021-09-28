# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.franka import Franka
from omni.isaac.core.objects import DynamicCube
import numpy as np


class Tower(BaseTask):
    def __init__(self) -> None:
        """[summary]
        """
        self.my_franka = None
        self.cube_1 = None
        self.cube_2 = None
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        super().set_up_scene(scene)
        self.my_franka = scene.add(Franka(stage=scene.stage, prim_path="/World/Franka", name="my_franka"))
        self.cube_1 = scene.add(
            DynamicCube(
                stage=self.scene.stage,
                name="cube_1",
                position=np.array([0.3, 0.3, 0.3]),
                prim_path="/World/Cube1",
                size=0.0515,
                color=np.array([0, 0, 255]),
            )
        )

        self.cube_2 = scene.add(
            DynamicCube(
                stage=self.scene.stage,
                name="cube_2",
                position=np.array([0.3, -0.3, 0.3]),
                prim_path="/World/Cube2",
                size=0.0515,
                color=np.array([255, 0, 0]),
            )
        )
        scene.add_ground_plane(
            size=50.0 / self.scene.stage_units_in_meters, thickness=0.5 / self.scene.stage_units_in_meters
        )
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self.my_franka.get_joints_state()
        cube_1_position, cube_1_orientation = self.cube_1.get_pose()
        cube_2_position, cube_2_orientation = self.cube_2.get_pose()
        end_effector_position, _ = self.my_franka.get_end_effector_pose()
        # self.get_pick_info()
        return {
            "cube_1": {
                "position": cube_1_position,
                "orientation": cube_1_orientation,
                "target_position": np.array([-0.3, 0.3, 0.065]),
            },
            "cube_2": {
                "position": cube_2_position,
                "orientation": cube_2_orientation,
                "target_position": np.array([-0.3, 0.3, 0.095]),
            },
            "my_franka": {"joint_positions": joints_state.positions, "end_effector_pose": end_effector_position},
        }

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def reset(self):
        self.my_franka.set_gripper_position(self.my_franka.gripper_open_position)
        return
