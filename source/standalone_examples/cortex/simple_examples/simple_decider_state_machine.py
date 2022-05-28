# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import numpy as np
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.df import DfNetwork, DfBindableState, DfStateMachineDecider, DfStateSequence
from omni.isaac.cortex.dfb import DfToolsContext


class ReachState(DfBindableState):
    def __init__(self, target_p):
        self.target_p = target_p

    def step(self):
        self.context.tools.commander.set_command(MotionCommand(target_pose=PosePq(self.target_p, None)))
        if np.linalg.norm(self.target_p - self.context.tools.commander.get_fk_p()) < 0.01:
            return None
        return self


def build_behavior(tools):
    tools.commander.set_target_position_only()
    root = DfStateMachineDecider(
        DfStateSequence([ReachState(np.array([0.2, -0.2, 0.01])), ReachState(np.array([0.6, 0.3, 0.6]))], loop=True)
    )
    return DfNetwork(decider=root, context=DfToolsContext(tools))
