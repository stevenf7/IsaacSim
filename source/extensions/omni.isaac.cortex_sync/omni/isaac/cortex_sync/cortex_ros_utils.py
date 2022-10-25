# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" A collection of ROS-dependent utilities for cortex.
"""

from collections import OrderedDict
import numpy as np

from cortex_control.msg import JointPosVelAccCommand
from std_msgs.msg import Header


class JointSubsetCommand:
    """ A tool to help create command messages for a specified subset of indices of a positon and
    velocity action.
    """

    def __init__(self, topic, indices):
        """ Create the subset command specifying the topic to be published on and the indices of the
        action we'll be extracting to create the command.

        Note this topic is simply stored in conjunction wtih this object. It isn't used in the
        command message creation process.
        """
        self.topic = topic
        self.indices = indices

    @property
    def is_empty(self):
        """ True if and only if there are no indices assigned to this subset.
        """
        return len(self.indices) == 0

    def pack_msg(self, joint_names, action, msg_id, stamp, period):
        """ Create the message corresponding to this set of indices.
        """
        msg = JointPosVelAccCommand()
        msg.period = period

        msg.id = msg_id
        msg.header = Header()
        msg.header.seq = msg_id
        msg.header.stamp = stamp

        q = action.joint_positions[self.indices]
        qd = action.joint_velocities[self.indices]

        msg.q = q
        msg.qd = qd
        msg.qdd = []  # Note, change to np.zeros(len(qd)) if using older builds of cortex_control_franka
        msg.names = [joint_names[i] for i in self.indices]
        msg.t = stamp

        return msg


def get_standard_split_joint_subset_commands(robot_info):
    """ Returns two subsets of joint commands, "active" joints controlled by the RMPs and "inactive"
    joints sent to a gripper controller.
    """
    n = robot_info.num_active_joints
    m = robot_info.robot.num_dof
    joint_subsets_commands = OrderedDict()
    joint_subsets_commands["arm"] = JointSubsetCommand("/rmpflow/commands/joint_command", list(range(0, n)))
    joint_subsets_commands["gripper"] = JointSubsetCommand("/rmpflow/commands/gripper", list(range(n, m)))
    return joint_subsets_commands
