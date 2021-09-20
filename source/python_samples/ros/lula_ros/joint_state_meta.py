# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import rospy
from sensor_msgs.msg import JointState
from util import wait_for_connections


class JointStateMeta(object):
    def __init__(self, topic):
        self.topic = topic
        self.sub = rospy.Subscriber(topic, JointState, self.callback)
        wait_for_connections(self.sub)

    def callback(self, msg):
        pass

    def num_publishers(self):
        return self.sub.get_num_connections()

    def validate_num_publishers(self):
        if self.num_publishers() > 1:
            print("ERROR -- multiple joint state publishers detected.")
            print("When connecting to a real-world robot, make sure to use ")
            print("the --is_real_world flag.")
            raise RuntimeError("Too many joint state publishers.")
