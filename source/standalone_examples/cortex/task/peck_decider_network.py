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

import omni
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid

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


def sample_target_p():
    min_x = 0.3
    max_x = 0.7
    min_y = -0.4
    max_y = 0.4

    pt = np.zeros(3)
    pt[0] = (max_x - min_x) * np.random.random_sample() + min_x
    pt[1] = (max_y - min_y) * np.random.random_sample() + min_y
    pt[2] = 0.01

    return pt


def make_target_rotation(target_p):
    return math_util.matrix_to_quat(
        math_util.make_rotation_matrix(az_dominant=np.array([0.0, 0.0, -1.0]), ax_suggestion=-target_p)
    )


class PeckContext(DfToolsContext):
    def __init__(self, tools):
        super().__init__(tools)

        self.is_done = True
        self.active_target_p = None

        self.monitors = [PeckContext.monitor_active_target_p]

    def monitor_active_target_p(self):
        if self.active_target_p is not None and self.is_near_obs(self.active_target_p):
            self.is_done = True

    def set_is_done(self):
        self.is_done = True

    def is_near_obs(self, p):
        for _, obs in self.tools.obstacles.items():
            obs_p, _ = obs.get_world_pose()
            if np.linalg.norm(obs_p - p) < 0.2:
                return True
        return False

    def sample_target_p_away_from_obs(self):
        target_p = sample_target_p()
        while self.is_near_obs(target_p):
            target_p = sample_target_p()
        return target_p

    def choose_next_target(self):
        self.active_target_p = self.sample_target_p_away_from_obs()


class PeckState(DfBindableState):
    def enter(self):
        target_p = self.context.active_target_p
        target_q = make_target_rotation(target_p)
        self.target = PosePq(target_p, target_q)
        self.approach_params = ApproachParams(direction=np.array([0.0, 0.0, -0.1]), std_dev=0.04)

    def step(self):
        # Send the command each cycle so exponential smoothing will converge.
        self.context.tools.commander.set_command(MotionCommand(self.target, approach_params=self.approach_params))
        target_dist = np.linalg.norm(self.context.tools.commander.get_fk_p() - self.target.p)

        if target_dist < 0.01:
            return None  # Exit
        return self  # Keep going


class ChooseTarget(DfAction):
    def step(self):
        self.context.is_done = False
        self.context.choose_next_target()


class Dispatch(DfDecider):
    """ The top-level decider.
    
    If the current peck task is done, then it will choose a target.  Otherwise, it executes the peck
    behavior. The peck behavior is a sequential state machine which 1. closes the gripper, 2. pecks,
    3. lifts the end-effector slightly, 4. writes to the context that it's done.
    
    This behavior by itself is equivalent to the state machine variant in peck_state_machine.py.
    However, the context is also continually monitoring the situation and if it sees that its
    current target is blocked, it'll set the context.is_done flag to True triggering this Dispatch
    decider to choose a new target.
    """

    def enter(self):
        self.add_child("choose_target", ChooseTarget())
        self.add_child(
            "peck",
            DfStateMachineDecider(
                DfStateSequence(
                    [
                        DfCloseGripper(width=0.0),
                        PeckState(),
                        DfTimedDeciderState(DfLift(height=0.05), activity_duration=0.25),
                        DfWriteContextState(lambda context: context.set_is_done()),
                    ]
                )
            ),
        )

    def decide(self):
        if self.context.is_done:
            return DfDecision("choose_target")
        else:
            return DfDecision("peck")


class PeckTask(CortexTask):
    """ CortexTask interface to constructing the peck behavior.
    """

    def build_behavior(self, tools):
        return DfNetwork(decider=Dispatch(), context=PeckContext(tools))


def main():
    world = World()
    robot = world.scene.add(Franka(prim_path="/World/franka", name="franka"))

    obstacles = {}
    width = 0.0515
    for i, x in enumerate(np.linspace(0.3, 0.7, 4)):
        tag = "cube{}".format(i)
        obj = DynamicCuboid(
            prim_path="/World/obs/{}".format(tag), name=tag, size=width, position=np.array([x, -0.4, width / 2])
        )
        obstacles[tag] = world.scene.add(obj)

    target_prim = VisualCuboid("/World/motion_commander_target", size=0.01, color=np.array([0.15, 0.15, 0.15]))
    commander = make_motion_commander(world.get_physics_dt(), robot, target_prim)
    world.add_task(PeckTask(name="peck", robot=robot, commander=commander, obstacles=obstacles))
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
