# Copyright (c) 2022, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
import omni.isaac.cortex.math_util as math_util


class Behavior(object):
    def __init__(self, tools):
        self.tools = tools

        target_p = np.array([0.5, 0.3, 0.01])
        target_q = math_util.matrix_to_quat(
            math_util.make_rotation_matrix(az_dominant=np.array([0.0, 0.0, -1.0]), ax_suggestion=-target_p)
        )
        self.target_pose = PosePq(target_p, target_q)
        self.approach_params = ApproachParams(direction=np.array([0.0, 0.0, -0.1]), std_dev=0.05)

    def tick(self):
        self.tools.commander.set_command(
            MotionCommand(target_pose=self.target_pose, approach_params=self.approach_params)
        )


def build_behavior(tools):
    return Behavior(tools)
