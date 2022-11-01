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
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid

# TODO: clean these up
from omni.isaac.cortex.df import DfNetwork, DfBindableState, DfStateMachineDecider, DfStateSequence
from omni.isaac.cortex.dfb import DfToolsContext
from omni.isaac.cortex.motion_commander import MotionCommand, PosePq


# TODO: clean these up
from omni.isaac.cortex.df import (
    DfNetwork,
    DfDecider,
    DfDecision,
    DfAction,
    DfBindableState,
    DfStateSequence,
    DfTimedDeciderState,
    DfStateMachineDecider,
    DfSetLockState,
    DfWriteContextState,
)
from omni.isaac.cortex.dfb import DfToolsContext, DfLift, DfCloseGripper, make_go_home
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.cortex_task import CortexTask
from omni.isaac.cortex.cortex_utils import configure_franka, make_motion_commander
from omni.isaac.cortex.tools import SteadyRate
from omni.isaac.franka import Franka


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
            MotionCommand(target_position=self.target_p, posture_config=self.posture_config)
        )

        if time.time() - self.entry_time < 2.0:
            return self
        return None


class NullspaceTask(CortexTask):
    """ CortexTask interface to constructing the peck behavior.
    """

    def build_behavior(self, tools):
        return DfNetwork(
            decider=DfStateMachineDecider(DfStateSequence([NullspaceShiftState()], loop=True)),
            context=DfToolsContext(tools),
        )


def main():
    world = World()
    robot = world.scene.add(Franka(prim_path="/World/franka", name="franka"))

    target_prim = VisualCuboid("/World/motion_commander_target", size=0.01, color=np.array([0.15, 0.15, 0.15]))
    commander = make_motion_commander(world.get_physics_dt(), robot, target_prim)

    world.add_task(NullspaceTask(name="nullspace", robot=robot, commander=commander))
    world.scene.add_default_ground_plane()

    world.reset()  # Reset to initialize the articulation handle. That allows us to configure it.
    configure_franka(robot, verbose=True)

    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt
    rate = SteadyRate(rate_hz)

    needs_reset = True  # Reset up front the first cycle through.
    while simulation_app.is_running():
        if world.is_playing():
            if needs_reset:
                print("<reset>")
                world.reset()
                needs_reset = False
        elif world.is_stopped():
            # Every time the world steps playing we'll need to reset again when it starts again.
            needs_reset = True

        world.step(render=True)
        rate.sleep()

    simulation_app.close()


if __name__ == "__main__":
    main()
