# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from .path_planning_interface import PathPlanner
from .articulation_subset import ArticulationSubset
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.utils.types import ArticulationAction

import numpy as np


class PathPlannerVisualizer:
    def __init__(self, robot_articulation, path_planner):
        self._robot_articulation = robot_articulation

        self._planner = path_planner

        self._articulation_controller = self._robot_articulation.get_articulation_controller()

        self._active_joints_view = ArticulationSubset(robot_articulation, path_planner.get_active_joints())
        self._watched_joints_view = ArticulationSubset(robot_articulation, path_planner.get_watched_joints())

    def compute_plan_as_articulation_actions(self, max_cspace_dist: float = 0.05):
        active_joint_positions = self._active_joints_view.get_joint_positions()

        watched_joint_positions = self._watched_joints_view.get_joint_positions()

        path = self._planner.compute_path(active_joint_positions, watched_joint_positions)
        if path is None:
            return []

        interpolated_path = self.interpolate_path(path, max_cspace_dist)

        actions_np_array = self._active_joints_view.map_to_articulation_order(interpolated_path)

        articulation_actions = [
            ArticulationAction(joint_positions=actions_np_array[i]) for i in range(len(actions_np_array))
        ]

        return articulation_actions

    def interpolate_path(self, path, max_cspace_dist: float = 0.05):
        if path.shape[0] == 0:
            return path

        interpolated_path = []
        for i in range(path.shape[0] - 1):
            n_pts = int(np.ceil(np.amax(abs(path[i + 1] - path[i])) / max_cspace_dist))
            interpolated_path.append(np.array(np.linspace(path[i], path[i + 1], num=n_pts, endpoint=False)))
        interpolated_path.append(path[np.newaxis, -1, :])

        interpolated_path = np.concatenate(interpolated_path)
        return interpolated_path

    def get_active_joints_subset(self) -> ArticulationSubset:
        """Get view into active joints

        Returns:
            ArticulationSubset: returns robot states for active joints in an order compatible with the MotionPolicy
        """
        return self._active_joints_view

    def get_watched_joints_subset(self) -> ArticulationSubset:
        return self._watched_joints_view

    def get_robot_articulation(self) -> Articulation:
        return self._robot_articulation

    def get_path_planner(self) -> PathPlanner:
        return self._planner
