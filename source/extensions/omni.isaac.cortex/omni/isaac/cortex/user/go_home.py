# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from df import DfAction, DfNetwork, DfStateMachineDecider, DfBindableState, DfStateSequence
import math_util
from motion_commander import MotionCommand, PosePq

reload_list = []


class Context:
    def __init__(self, tools):
        self.tools = tools


class GoHomeState(DfBindableState):
    def __init__(self):
        super().__init__()
        self.retracted_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75])

    def step(self):
        retracted_config = self.retracted_config

        p = np.array([2.67799703e-01, 0.0, 4.28357714e-01])
        ay = np.array([-3.21689980e-02, 9.99373550e-01, -1.47533814e-02])
        az = np.array([4.16870863e-01, 0.0, -9.08965722e-01])
        ax = np.cross(ay, az)
        R = math_util.pack_R(ax, ay, az)

        # Check whether the end-effector is reasonably close to the target. If so, we're done. Stop
        # setting commands. The user can take over and move the prim manually.
        target_T = math_util.pack_Rp(R, p)
        eff_T = self.context.tools.commander.get_fk_T()
        if np.linalg.norm(eff_T - target_T) < 0.01:
            return None

        command = MotionCommand(PosePq(p, math_util.matrix_to_quat(R)), posture_config=retracted_config)
        self.context.tools.commander.set_command(command)

        return self


def make_go_home():
    return DfStateMachineDecider(DfStateSequence([GoHomeState()]))


def build_behavior(tools):
    behavior = DfNetwork(make_go_home())
    behavior.bind_context(Context(tools))
    return behavior
