# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import rospy
from lula_ros.msg import JointPosVelAccCommand, LulaCommandAck


class InterpolatedCommandListener(object):
    def __init__(self, robot):
        self.robot = robot
        self.dof_states = robot.joint_states
        self.interpolated_state = None
        self.interpolated_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/interpolated", JointPosVelAccCommand, self.interpolated_command_callback
        )

    def interpolated_command_callback(self, data):
        # Every callback replaces the data. Grabing it before using it ensures
        # synchronization.
        self.interpolated_state = data

    def get_latest_interpolated_dof_states(self):
        if self.interpolated_state is not None:
            # Grab it so it doesn't change out from under us.
            interpolated_state = self.interpolated_state
            for j in range(self.robot.num_joints):
                index = self.robot.joint_indices[j]
                self.dof_states["pos"][index] = interpolated_state.q[j]
                self.dof_states["vel"][index] = interpolated_state.qd[j]
            return self.dof_states
        else:
            return None
