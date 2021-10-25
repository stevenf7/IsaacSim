# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseController
from omni.isaac.core.utils.types import ArticulationAction
from typing import Optional
from omni.isaac.core.utils.rotations import quat_to_rot_matrix, euler_angles_to_quat
from omni.isaac.dynamic_control import _dynamic_control
import numpy as np
import lula


class InverseKinematicsSolver(BaseController):
    def __init__(self, name, robot_urdf_path, robot_description_yaml_path, robot_prim_path, end_effector_frame_name):
        BaseController.__init__(self, name)
        self._robot_description = lula.load_robot(robot_description_yaml_path, robot_urdf_path)
        self._kinematics = self._robot_description.kinematics()
        self._end_effector_frame_name = end_effector_frame_name
        self._config = lula.CyclicCoordDescentIkConfig()
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        handle = self._dc_interface.get_articulation(robot_prim_path)
        self._active_joints = [
            self._robot_description.c_space_coord_name(i) for i in range(self._robot_description.num_c_space_coords())
        ]
        self._active_joints_indices = [
            self._dc_interface.find_articulation_dof_index(handle, joint) for joint in self._active_joints
        ]
        self._num_dof = self._dc_interface.get_articulation_dof_count(handle)
        return

    def forward(
        self, target_end_effector_position: np.ndarray, target_end_effector_orientation: Optional[np.ndarray] = None
    ):
        if target_end_effector_orientation is None:
            target_end_effector_orientation = euler_angles_to_quat(np.array([0, np.pi, 0]))
        rot = np.array(quat_to_rot_matrix(target_end_effector_orientation), dtype=np.float64).reshape(3, 3)
        translation = np.array(target_end_effector_position, dtype=np.float64).reshape(3, 1)
        target_pose = lula.Pose3(lula.Rotation3(rot), translation)
        results = lula.compute_ik_ccd(self._kinematics, target_pose, self._end_effector_frame_name, self._config)
        self._config.cspace_seeds = [results.cspace_position]
        target_joint_positions = [None] * self._num_dof
        for i in range(len(self._active_joints_indices)):
            target_joint_positions[self._active_joints_indices[i]] = results.cspace_position[i]
        return ArticulationAction(joint_positions=target_joint_positions)

    def reset(self):
        return
