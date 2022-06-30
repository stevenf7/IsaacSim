#
# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import carb
from typing import List, Union

import lula
from ..path_planning_interface import PathPlanner
from .interface_helper import LulaInterfaceHelper
from omni.isaac.core.utils.numpy.rotations import quats_to_rot_matrices
from omni.isaac.core import objects


class RRT(LulaInterfaceHelper, PathPlanner):
    def __init__(self, robot_description_path: str, urdf_path: str, rrt_config_path: str, end_effector_frame_name: str):

        robot_description = lula.load_robot(robot_description_path, urdf_path)
        self.end_effector_frame_name = end_effector_frame_name

        LulaInterfaceHelper.__init__(self, robot_description)

        world_view = self._world.add_world_view()

        self.rrt_config_path = rrt_config_path

        self._rrt = lula.create_motion_planner(self.rrt_config_path, self._robot_description, world_view)

        self._rrt.set_param("task_space_frame_name", self.end_effector_frame_name)
        self._seed = 123456

        self._plan = None

        self._cspace_target = None
        self._taskspace_target_position = None
        self._taskspace_target_rotation = None

    def compute_path(self, active_joint_positions, watched_joint_positions) -> np.array:
        __doc__ = PathPlanner.compute_path.__doc__

        active_joint_positions = active_joint_positions.astype(np.float64)
        if self._taskspace_target_position is None and self._cspace_target is not None:
            self._generate_plan_to_cspace_target(active_joint_positions)
        elif self._taskspace_target_position is None:
            self._plan = None
        else:
            self._generate_plan_to_taskspace_target(active_joint_positions)

        return self._plan

    def set_robot_base_pose(self, robot_position: np.array, robot_orientation: np.array) -> None:
        __doc__ = LulaInterfaceHelper.set_robot_base_pose.__doc__

        return LulaInterfaceHelper.set_robot_base_pose(self, robot_position, robot_orientation)

    def set_cspace_target(self, active_joint_targets: np.array) -> None:
        __doc__ = PathPlanner.set_cspace_target.__doc__

        self._cspace_target = active_joint_targets
        self._taskspace_target_position = None
        self._taskspace_target_rotation = None

    def set_end_effector_target(self, target_translation, target_orientation=None) -> None:
        __doc__ = PathPlanner.set_end_effector_target.__doc__

        if target_translation is not None:
            self._taskspace_target_position = (target_translation * self._meters_per_unit).astype(np.float64)
        else:
            self._taskspace_target_position = None

        if target_orientation is not None:
            target_rotation = quats_to_rot_matrices(target_orientation)
        else:
            target_rotation = None

        self._taskspace_target_rotation = target_rotation
        self._cspace_target = None

        if self._taskspace_target_rotation is not None:
            carb.log_warn(
                "Lula's RRT implementation does not currently support orientation targets.  The generated plan will ignore the orientation target"
            )

    def get_active_joints(self) -> List:
        __doc__ = PathPlanner.get_active_joints.__doc__

        return LulaInterfaceHelper.get_active_joints(self)

    def get_watched_joints(self) -> List:
        return LulaInterfaceHelper.get_watched_joints(self)

    def add_obstacle(self, obstacle: objects, static: bool = False) -> bool:
        __doc__ = PathPlanner.add_obstacle.__doc__
        return PathPlanner.add_obstacle(self, obstacle, static)

    def add_cuboid(
        self,
        cuboid: Union[objects.cuboid.DynamicCuboid, objects.cuboid.FixedCuboid, objects.cuboid.VisualCuboid],
        static: bool = False,
    ) -> bool:
        return LulaInterfaceHelper.add_cuboid(self, cuboid, static)

    def add_sphere(
        self, sphere: Union[objects.sphere.DynamicSphere, objects.sphere.VisualSphere], static: bool = False
    ) -> bool:
        return LulaInterfaceHelper.add_sphere(self, sphere, static)

    def add_capsule(
        self, capsule: Union[objects.capsule.DynamicCapsule, objects.capsule.VisualCapsule], static: bool = False
    ) -> bool:
        return LulaInterfaceHelper.add_capsule(self, capsule, static)

    def add_ground_plane(self, ground_plane: objects.ground_plane.GroundPlane) -> bool:
        return LulaInterfaceHelper.add_ground_plane(self, ground_plane)

    def disable_obstacle(self, obstacle: objects) -> bool:
        return LulaInterfaceHelper.disable_obstacle(self, obstacle)

    def enable_obstacle(self, obstacle: objects) -> bool:
        return LulaInterfaceHelper.enable_obstacle(self, obstacle)

    def remove_obstacle(self, obstacle: objects) -> bool:
        return LulaInterfaceHelper.remove_obstacle(self, obstacle)

    def update_world(self, updated_obstacles: List = None) -> None:
        LulaInterfaceHelper.update_world(self, updated_obstacles)
        self._rrt.update_world_view()

    def reset(self) -> None:
        LulaInterfaceHelper.reset(self)

        self._rrt = lula.create_motion_planner(
            self.rrt_config_path, self._robot_description, self._world.add_world_view()
        )

        self._rrt.set_param("task_space_frame_name", self.end_effector_frame_name)
        self._seed = 123456

    def set_max_iterations(self, max_iter: int) -> None:
        """Set the maximum number of iterations of RRT before a failure is returned

        Args:
            max_iter (int): Maximum number of iterations of RRT before a failure is returned.
                The time it takes to return a failure scales quadratically with max_iter
        """
        self._rrt.set_param("max_iterations", max_iter)

    def set_random_seed(self, random_seed: int) -> None:
        """Set the random seed that RRT uses to generate a solution

        Args:
            random_seed (int): Random seed used to compute a path to a target pose
        """
        self._seed = random_seed

    def _generate_plan_to_cspace_target(self, joint_positions):
        if self._cspace_target is None:
            self._plan = None
            return
        plan = self._rrt.plan_to_cspace_target(joint_positions, self._cspace_target)
        if plan.path_found:
            self._plan = np.array(plan.path)
        else:
            self._plan = None

    def _generate_plan_to_taskspace_target(self, joint_positions):
        if self._taskspace_target_position is None:
            self._plan = None
            return

        trans_rel, _ = LulaInterfaceHelper._get_pose_rel_robot_base(self, self._taskspace_target_position, None)

        self._rrt.set_param("seed", self._seed)
        import time

        s = time.time()
        plan = self._rrt.plan_to_task_space_target(joint_positions, trans_rel, generate_interpolated_path=False)

        if plan.path_found:
            self._plan = np.array(plan.path)
        else:
            self._plan = None
