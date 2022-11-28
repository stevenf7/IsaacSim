# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np
import time

# TODO: clean these up
import omni
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid

# TODO: clean these up
from omni.isaac.cortex.df import DfNetwork, DfState, DfStateMachineDecider, DfStateSequence
from omni.isaac.cortex.dfb import DfContext
from omni.isaac.cortex.motion_commander import MotionCommand, PosePq


# TODO: clean these up
from omni.isaac.cortex.df import (
    DfNetwork,
    DfDecider,
    DfDecision,
    DfAction,
    DfState,
    DfStateSequence,
    DfTimedDeciderState,
    DfStateMachineDecider,
    DfSetLockState,
    DfWriteContextState,
)
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.cortex_world import CortexWorld, LogicalStateMonitor, Behavior
from omni.isaac.cortex.tools import SteadyRate
from omni.isaac.cortex.robot import add_franka_to_stage


class NullspaceShiftState(DfState):
    def __init__(self):
        super().__init__()
        self.config_mean = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75])
        self.target_p = np.array([0.7, 0.0, 0.5])
        self.construction_time = time.time()

    def enter(self):
        self.posture_config = self.config_mean + np.random.randn(7)
        self.entry_time = time.time()

        gripper = self.context.robot.gripper
        if gripper.get_width() > 0.05:
            gripper.close(speed=0.5)
        else:
            gripper.open(speed=0.1)

        print("[%f] <enter> sampling posture config" % (self.entry_time - self.construction_time))

    def step(self):
        self.context.robot.arm.send_end_effector(target_position=self.target_p, posture_config=self.posture_config)

        if time.time() - self.entry_time < 2.0:
            return self
        return None


def main():
    world = CortexWorld()
    robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/franka"))

    decider_network = DfNetwork(
        decider=DfStateMachineDecider(DfStateSequence([NullspaceShiftState()], loop=True)), context=DfContext(robot)
    )
    world.add_behavior(Behavior("nullspace_behavior", decider_network))
    world.scene.add_default_ground_plane()

    world.step_loop_runner(simulation_app)

    simulation_app.close()


if __name__ == "__main__":
    main()
