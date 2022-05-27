# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import numpy as np
import time

from omni.isaac.cortex.df import DfNetwork, DfBindableState, DfStateMachineDecider, DfStateSequence
from omni.isaac.cortex.dfb import DfToolsContext
from omni.isaac.cortex.motion_commander import MotionCommand, PosePq


class NullspaceShiftState(DfBindableState):
    def __init__(self):
        super().__init__()
        self.config_mean = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75])
        self.target_p = np.array([0.7, 0.0, 0.5])
        self.construction_time = time.time()

    def enter(self):
        self.posture_config = self.config_mean + np.random.randn(7)
        self.entry_time = time.time()
        print("[%f] <enter> sampling posture config" % (self.entry_time - self.construction_time))

    def step(self):
        self.context.tools.commander.set_command(
            MotionCommand(target_pose=PosePq(self.target_p, None), posture_config=self.posture_config)
        )

        if time.time() - self.entry_time < 2.0:
            return self
        return None


def build_behavior(tools):
    tools.commander.set_target_position_only()
    return DfNetwork(
        decider=DfStateMachineDecider(DfStateSequence([NullspaceShiftState()], loop=True)),
        context=DfToolsContext(tools),
    )
