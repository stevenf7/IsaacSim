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

from omni.isaac.core.objects import VisualSphere
from omni.isaac.cortex.cortex_world import CortexWorld
from omni.isaac.cortex.df import DfNetwork, DfState, DfStateMachineDecider
from omni.isaac.cortex.dfb import DfContext, DfDiagnosticsMonitor
from omni.isaac.cortex.robot import add_franka_to_stage


class FollowState(DfState):
    """ The context object is available as self.context. We have access to everything in the context
    object, which in this case is everything in the robot object (the command API and the follow
    sphere).
    """

    @property
    def robot(self):
        return self.context.robot

    @property
    def follow_sphere(self):
        return self.context.robot.follow_sphere

    def enter(self):
        self.follow_sphere.set_world_pose(*self.robot.arm.get_fk_pq().as_tuple())

    def step(self):
        target_position, _ = self.follow_sphere.get_world_pose()
        self.robot.arm.send_end_effector(target_position=target_position)
        return self  # Always transition back to this state.


class FollowContextDiagnosticsMonitor(DfDiagnosticsMonitor):
    def print_diagnostics(self, context):
        print("\n================== logical state ===================")
        print("time since start: {:.2f}".format(self.time_since_start))
        print("is_target_reached: {}".format(context.is_target_reached))


class FollowContext(DfContext):
    def __init__(self, robot):
        super().__init__(robot)

        self.reset()

        self.add_monitors(
            [FollowContext.monitor_end_effector, FollowContext.monitor_gripper, self.diagnostics_monitor.monitor]
        )

    def reset(self):
        self.is_target_reached = False

        self.robot.gripper.close()
        self.gripper_state = "closing"

        self.diagnostics_monitor = FollowContextDiagnosticsMonitor()

    def monitor_end_effector(self):
        eff_p = self.robot.arm.get_fk_p()
        target_p, _ = self.robot.follow_sphere.get_world_pose()
        self.is_target_reached = np.linalg.norm(target_p - eff_p) < 0.01

    def monitor_gripper(self):
        if self.gripper_state == "opening" and self.robot.gripper.is_open():
            self.robot.gripper.close()
            self.gripper_state = "closing"
        elif self.gripper_state == "closing" and self.robot.gripper.is_closed():
            self.robot.gripper.open()
            self.gripper_state = "opening"


def main():
    world = CortexWorld()
    robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/Franka"))

    # Add a sphere to the scene to follow, and store it off in a new member as part of the robot.
    robot.follow_sphere = world.scene.add(
        VisualSphere(
            name="follow_sphere", prim_path="/World/FollowSphere", radius=0.02, color=np.array([0.7, 0.0, 0.7])
        )
    )
    world.scene.add_default_ground_plane()

    # Add a simple state machine decider network with the single state defined above. This state
    # will be persistently stepped because it always returns itself.
    # world.add_logical_state_monitor(LogicalStateMonitor("ls_monitors", decider_network.context))
    world.add_decider_network(DfNetwork(DfStateMachineDecider(FollowState()), context=FollowContext(robot)))

    world.run(simulation_app)
    simulation_app.close()


if __name__ == "__main__":
    main()
