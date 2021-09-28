# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.ur10.controllers.rmpflow_ik import RMPFlowIKSolver
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import numpy as np
from omni.isaac.core.utils.rotations import quat_to_rot_matrix


class RMPFlowPickPlace(RMPFlowIKSolver):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(
        self,
        name,
        mg_extension_path,
        dc_interface,
        stage,
        robot_prim,
        gripper_controller,
        gripper_length,
        approach="top",
    ):
        super().__init__(
            name=name,
            mg_extension_path=mg_extension_path,
            dc_interface=dc_interface,
            stage=stage,
            robot_prim=robot_prim,
            with_short_gripper=True,
        )
        self._event = 0
        self._t = 0
        # TODO: change values with USD
        self._h1 = 0.6 * 100
        self._h0 = None
        self._event_velocities = [0.008, 0.005, 0.3, 0.0025, 0.002, 0.0025, 1, 0.008, 0.08]
        self._gripper_controller = gripper_controller
        self._gripper_length = gripper_length
        self._approach = approach
        self._pause = False
        """
        - Phase 0: Move end_effector above the cube center.
        - Phase 1: Lower end_effector down to encircle the target cube
        - Phase 2: close grip.
        - Phase 3: Move end_effector up again, keeping the grip tight (lifting the block).
        - Phase 4: Smoothly move the end_effector toward the goal xy, keeping the height constant.
        - Phase 5: Move end_effector vertically toward goal height.
        - Phase 6: loosen the grip.
        - Phase 7: Move end_effector vertically up again
        - Phase 8: Move end_effector towards the old xy position. 
        """
        return

    def is_paused(self):
        return self._pause

    def get_current_event(self):
        return self._event

    def forward(
        self,
        cube_position,
        cube_orientation,
        cube_target_position,
        current_joint_positions,
        cube_size,
        contact_point_offset=None,
        contact_height=None,
    ):
        if self._pause or self._event >= len(self._event_velocities):
            target_joint_positions = [None] * current_joint_positions.shape[0]
            return ArticulationAction(joint_positions=target_joint_positions)
        if self._approach == "side":
            approach_angle = np.array([np.pi, 0, np.pi / 2.0])
            target_height = self._get_target_hs(cube_target_position[2])
        elif self._approach == "top":
            approach_angle = np.array([0, np.pi / 2.0, 0])
            target_height = self._get_target_hs(cube_target_position[2] + (cube_size[2] / 2.0))

        if self._event < 2:
            if self._approach == "side":
                pose = np.eye(4, dtype=np.float64)
                pose[:3, :3] = quat_to_rot_matrix(cube_orientation)
                pose[:3, 3] = cube_position
                if contact_point_offset is None:
                    contact_point_offset = np.array([0, cube_size[1] / 2.0, cube_size[2] / 2.0, 1])
                else:
                    contact_point_offset_new = np.zeros(4)
                    contact_point_offset_new[:3] = contact_point_offset
                    contact_point_offset_new[3] = 1
                    contact_point_offset = contact_point_offset_new
                mid_point = np.transpose(np.matmul(pose, np.reshape(contact_point_offset, newshape=[4, 1])))
                self._current_target_x = mid_point[0, 0]
                self._current_target_y = mid_point[0, 1]
                if contact_height is None:
                    self._h0 = cube_position[2]
                else:
                    self._h0 = contact_height
            elif self._approach == "top":
                self._current_target_x = cube_position[0]
                self._current_target_y = cube_position[1]
                if contact_height is None:
                    self._h0 = cube_position[2] + (cube_size[2] / 2.0)
                else:
                    self._h0 = contact_height
        interpolated_xy = self._get_interpolated_xy(
            cube_target_position[0], cube_target_position[1], self._current_target_x, self._current_target_y
        )
        position_target = np.array([interpolated_xy[0], interpolated_xy[1], target_height])
        if self._event == 2:
            if not self._gripper_controller.is_gripper_closed():
                self._gripper_controller.close_gripper()
            target_joint_positions = [None] * current_joint_positions.shape[0]
            target_joint_positions = ArticulationAction(joint_positions=target_joint_positions)
        elif self._event == 6:
            if self._gripper_controller.is_gripper_closed():
                self._gripper_controller.open_gripper()
            target_joint_positions = [None] * current_joint_positions.shape[0]
            target_joint_positions = ArticulationAction(joint_positions=target_joint_positions)
        else:
            target_joint_positions = super().forward(
                current_joint_positions=current_joint_positions,
                target_end_effector_position=position_target,
                target_end_effector_orientation=euler_angles_to_quat(approach_angle),
            )
        self._t += self._event_velocities[self._event]
        if self._t >= 1.0:
            self._event += 1
            self._t -= 1.0
        return target_joint_positions

    def _get_interpolated_xy(self, target_x, target_y, current_x, current_y):
        alpha = self._get_alpha()
        xy_target = (1 - alpha) * np.array([current_x, current_y]) + alpha * np.array([target_x, target_y])
        return xy_target

    def _get_alpha(self):
        if self._event < 4:
            return 0
        elif self._event == 4:
            return self._mix_sin(self._t)
        elif self._event in [5, 6, 7]:
            return 1.0
        elif self._event == 8:
            return 1 - self._mix_sin(self._t)
        else:
            raise ValueError()

    def _get_target_hs(self, target_height):
        if self._event == 0:
            h = self._h1
        elif self._event == 1:
            a = self._mix_sin(max(0, self._t))
            h = self._combine_convex(self._h1, self._h0, a)
        elif self._event == 2:
            h = self._h0
        elif self._event == 3:
            a = self._mix_sin(max(0, self._t))
            h = self._combine_convex(self._h0, self._h1, a)
        elif self._event == 4:
            h = self._h1
        elif self._event == 5:
            h = self._combine_convex(self._h1, target_height, self._mix_sin(self._t))
        elif self._event == 6:
            h = target_height
        elif self._event == 7:
            h = self._combine_convex(target_height, self._h1, self._mix_sin(self._t))
        elif self._event == 8:
            h = self._h1
        else:
            raise ValueError()
        return h

    def _mix_sin(self, t):
        return 0.5 * (1 - np.cos(t * np.pi))

    def _combine_convex(self, a, b, alpha):
        return (1 - alpha) * a + alpha * b

    def reset(self, approach=None):
        super().reset()
        self._event = 0
        self._t = 0
        if approach is not None:
            self._approach = approach
        self._pause = False
        return

    def is_done(self):
        if self._event >= len(self._event_velocities):
            return True
        else:
            return False

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False
