# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from collections import OrderedDict
import numpy as np

from lula_ros.msg import JointPosVelAccCommand
from std_msgs.msg import Header


class JointSubsetCommand:
    def __init__(self, topic, indices):
        self.topic = topic
        self.indices = indices

    def pack_msg(self, joint_names, action, msg_id, stamp, period):
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
        # TODO: hack - convert this back to []. Adding this here as a hack to get it to work with an
        # old build of lula_ros_franka.
        msg.qdd = np.zeros(len(qd))
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
