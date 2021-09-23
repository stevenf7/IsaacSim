# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.dofbot.controllers.rmpflow_ik import RMPFlowIKSolver
from omni.isaac.dofbot.controllers.gripper_controller import GripperController
from omni.isaac.core.utils.types import ArticulationAction
import numpy as np


class RMPFlowPickPlace(RMPFlowIKSolver):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, mg_extension_path, dc_interface, stage, robot_prim, gripper_dof_indices):
        super().__init__(
            name=name,
            mg_extension_path=mg_extension_path,
            dc_interface=dc_interface,
            stage=stage,
            robot_prim=robot_prim,
        )
        self._event = 0
        self._t = 0
        # TODO: change values with USD
        self._h1 = 0.2 * 100
        self._h0 = None
        self._event_velocities = [0.008, 0.005, 0.005, 0.0025, 0.002, 0.0025, 0.005, 0.008, 0.08]
        self._gipper_controller = GripperController(name="gripper_controller", gripper_dof_indices=gripper_dof_indices)
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

    def forward(self, cube_position, cube_orientation, cube_target_position, current_joint_positions):
        # TODO: orientation is not working with the motion generation for some reason, ignored for now
        if self._event >= len(self._event_velocities):
            target_joint_positions = [None] * current_joint_positions.shape[0]
            return ArticulationAction(joint_positions=target_joint_positions)
        if self._event < 2:
            self._current_target_x = cube_position[0]
            self._current_target_y = cube_position[1]
            self._h0 = cube_position[2]

        interpolated_xy = self._get_interpolated_xy(
            cube_target_position[0], cube_target_position[1], self._current_target_x, self._current_target_y
        )

        target_height = self._get_target_hs(cube_target_position[2])
        position_target = np.array([interpolated_xy[0], interpolated_xy[1], target_height])

        if self._event == 2:
            target_joint_positions = self._gipper_controller.forward(
                current_joint_positions=current_joint_positions, deltas=(0.05, -0.05)
            )
        elif self._event == 6:
            target_joint_positions = self._gipper_controller.forward(
                current_joint_positions=current_joint_positions, deltas=(-0.05, 0.05)
            )
        else:
            target_joint_positions = super().forward(
                current_joint_positions=current_joint_positions, target_end_effector_position=position_target
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

    def reset(self):
        super().reset()
        self._event = 0
        self._t = 0
        return

    def is_done(self):
        if self._event >= len(self._event_velocities):
            return True
        else:
            return False
