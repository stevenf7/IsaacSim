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
from omni.isaac.dofbot import DofBot
from omni.isaac.core.objects import DynamicCube
import numpy as np


class PickPlace(BaseTask):
    def __init__(self) -> None:
        """[summary]
        """
        self.my_dofbot = None
        self.cube = None
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        # TODO: change values with USD
        super().set_up_scene(scene)
        self.my_dofbot = scene.add(DofBot(stage=scene.stage, prim_path="/World/DofBot", name="my_dofbot"))
        self.cube = scene.add(
            DynamicCube(
                stage=self.scene.stage,
                name="cube_1",
                position=np.array([0.31, 0, 0.025 / 2.0]) * 100,
                prim_path="/World/Cube",
                size=0.025 * 100,
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
        joints_state = self.my_dofbot.get_joints_state()
        cube_position, cube_orientation = self.cube.get_pose()
        end_effector_position, _ = self.my_dofbot.get_end_effector_pose()
        # TODO: change values with USD
        return {
            "cube_1": {
                "position": cube_position,
                "orientation": cube_orientation,
                "target_position": np.array([-0.31, 0, 0.05]) * 100,
            },
            "my_dofbot": {"joint_positions": joints_state.positions, "end_effector_pose": end_effector_position},
        }

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def reset(self):
        self.my_dofbot.set_gripper_position(self.my_dofbot.gripper_open_position)
        return
