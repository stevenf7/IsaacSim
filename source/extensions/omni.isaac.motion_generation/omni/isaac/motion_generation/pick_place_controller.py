# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseController
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import numpy as np


class PickPlaceController(BaseController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, ik_solver, gripper_controller, start_picking_height=None, event_velocities=None):
        BaseController.__init__(self, name=name)
        self._event = 0
        self._t = 0
        self._h1 = start_picking_height
        if self._h1 is None:
            self._h1 = 0.3 / get_stage_units()
        self._h0 = None
        self._event_velocities = event_velocities
        if self._event_velocities is None:
            self._event_velocities = [0.008, 0.005, 0.1, 0.0025, 0.001, 0.0025, 1, 0.008, 0.08]
        else:
            if not isinstance(self._event_velocities, np.ndarray) and not isinstance(self._event_velocities, list):
                raise Exception("event velocities need to be list or numpy array")
            elif isinstance(self._event_velocities, np.ndarray):
                self._event_velocities = self._event_velocities.tolist()
            if len(self._event_velocities) != 9:
                raise Exception("event velocities need have length of 9")
        self._ik_solver = ik_solver
        self._gripper_controller = gripper_controller
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
        picking_position,
        placing_position,
        current_joint_positions,
        end_effector_offset=None,
        end_effector_orientation=None,
    ):
        if end_effector_offset is None:
            end_effector_offset = np.array([0, 0, 0])
        if self._pause or self._event >= len(self._event_velocities):
            target_joint_positions = [None] * current_joint_positions.shape[0]
            return ArticulationAction(joint_positions=target_joint_positions)

        if self._event < 2:
            self._current_target_x = picking_position[0]
            self._current_target_y = picking_position[1]
            self._h0 = picking_position[2]
        # TODO: take into account cube orientation

        interpolated_xy = self._get_interpolated_xy(
            placing_position[0], placing_position[1], self._current_target_x, self._current_target_y
        )
        target_height = self._get_target_hs(placing_position[2])
        position_target = np.array(
            [
                interpolated_xy[0] + end_effector_offset[0],
                interpolated_xy[1] + end_effector_offset[1],
                target_height + end_effector_offset[2],
            ]
        )
        if self._event == 2:
            target_joint_positions = self._gripper_controller.forward(
                action="close", current_joint_positions=current_joint_positions
            )
        elif self._event == 6:
            target_joint_positions = self._gripper_controller.forward(
                action="open", current_joint_positions=current_joint_positions
            )
        else:
            if end_effector_orientation is None:
                end_effector_orientation = euler_angles_to_quat(np.array([0, np.pi, 0]))
            target_joint_positions = self._ik_solver.forward(
                target_end_effector_position=position_target, target_end_effector_orientation=end_effector_orientation
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
            return 1
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

    def reset(self, start_picking_height=None, event_velocities=None):
        BaseController.reset(self)
        self._gripper_controller.reset()
        self._ik_solver.reset()
        self._event = 0
        self._t = 0
        if start_picking_height is not None:
            self._h1 = start_picking_height
        self._pause = False
        if event_velocities is not None:
            self._event_velocities = event_velocities
            if not isinstance(self._event_velocities, np.ndarray) or not isinstance(self._event_velocities, list):
                raise Exception("event velocities need to be list or numpy array")
            elif isinstance(self._event_velocities, np.ndarray):
                self._event_velocities = self._event_velocities.tolist()
            if len(self._event_velocities) == 9:
                raise Exception("event velocities need have length of 9")
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
