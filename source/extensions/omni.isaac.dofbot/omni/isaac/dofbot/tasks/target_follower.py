# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.dofbot import DofBot
from omni.isaac.core.objects import VisualCube, DynamicCube
import numpy as np


class TargetFollower(BaseTask):
    def __init__(self) -> None:
        """[summary]
        """
        self.my_dofbot = None
        self.target_cube = None
        self.obstacle_cubes = dict()
        return

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        # TODO: change values with USD
        super().set_up_scene(scene)
        self.my_dofbot = scene.add(DofBot(stage=scene.stage, prim_path="/World/DofBot", name="my_dofbot"))
        self.target_cube = scene.add(
            VisualCube(
                stage=scene.stage,
                name="target_cube",
                prim_path="/World/TargetCube",
                position=np.array([0, 0.1, 0.3]) * 100,
                orientation=np.array([0, 0, 0, 1]),
                color=np.array([255, 0, 0]),
                size=0.02 * 100,
            )
        )
        scene.add_ground_plane(
            size=50.0 / self.scene.stage_units_in_meters, thickness=0.5 / self.scene.stage_units_in_meters
        )
        return

    def add_obstacle(self, position: np.ndarray = np.array([0.1, 0.1, 1.0])):
        """[summary]

        Args:
            position (np.ndarray, optional): [description]. Defaults to np.array([0.1, 0.1, 1.0]).
        """
        # TODO: change values with USD
        cube = self.scene.add(
            DynamicCube(
                stage=self.scene.stage,
                name="cube_" + str(len(self.obstacle_cubes)),
                position=position,
                prim_path="/World/ObstacleCube_" + str(len(self.obstacle_cubes)),
                size=0.1 * 100,
                color=np.array([0, 0, 255]),
            )
        )
        self.obstacle_cubes[cube.name] = cube
        return cube

    def remove_obstacle(self, name: Optional[str] = None) -> None:
        """[summary]

        Args:
            name (Optional[str], optional): [description]. Defaults to None.
        """
        if name is not None:
            self.scene.remove_object(name)
            del self.obstacle_cubes[name]
        else:
            obstacle_to_delete = list(self.obstacle_cubes.keys())[0]
            self.scene.remove_object(obstacle_to_delete)
            del self.obstacle_cubes[obstacle_to_delete]
        return

    def get_obstacle_to_delete(self):
        obstacle_to_delete = list(self.obstacle_cubes.keys())[0]
        return self.scene.get_object(obstacle_to_delete)

    def obstacles_exist(self) -> bool:
        if len(self.obstacle_cubes) > 0:
            return True
        else:
            return False

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        joints_state = self.my_dofbot.get_joints_state()
        target_cube_position, _ = self.target_cube.get_usd_pose()
        return {
            "my_dofbot": {
                "joint_positions": np.array(joints_state.positions),
                "joint_velocities": np.array(joints_state.velocities),
            },
            "target_cube": {"position": np.array(target_cube_position)},
        }

    def target_reached(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        end_effector_position, _ = self.my_dofbot.end_effector.get_pose()
        target_cube_position, _ = self.target_cube.get_usd_pose()
        # TODO: change values with USD
        if np.mean(np.abs(np.array(end_effector_position) - np.array(target_cube_position))) < 0.03 * 100:
            return True
        else:
            return False

    def step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        if self.target_reached():
            self.target_cube.set_usd_color(color=np.array([0, 255, 0]))
        else:
            self.target_cube.set_usd_color(color=np.array([255, 0, 0]))
        return

    def reset(self) -> None:
        """[summary]
        """
        return

    def cleanup(self) -> None:
        obstacles_to_delete = list(self.obstacle_cubes.keys())
        for obstacle_to_delete in obstacles_to_delete:
            self.scene.remove_object(obstacle_to_delete)
            del self.obstacle_cubes[obstacle_to_delete]
        return
