# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import numpy as np
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.df import DfState


class StateMachine:
    def __init__(self, init_state):
        self.needs_entry = True
        self.state = init_state

    def tick(self):
        if self.state is None:
            return

        if self.needs_entry:
            self.state.enter()
            self.needs_entry = False

        new_state = self.state.step()

        if new_state != self.state:
            self.state.exit()
            self.state = new_state
            self.needs_entry = True


class ReachState(DfState):
    def __init__(self, target_p, tools):
        self.target_p = target_p
        self.tools = tools
        self.next_state = None

    def step(self):
        self.tools.commander.set_command(MotionCommand(target_pose=PosePq(self.target_p, None)))
        if np.linalg.norm(self.target_p - self.tools.commander.get_fk_p()) < 0.01:
            return self.next_state
        return self


def build_behavior(tools):
    tools.commander.set_target_position_only()

    p1 = np.array([0.2, -0.2, 0.01])
    p2 = np.array([0.6, 0.3, 0.6])
    state1 = ReachState(p1, tools)
    state2 = ReachState(p2, tools)

    state1.next_state = state2
    state2.next_state = state1
    return StateMachine(state1)
