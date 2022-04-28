# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import math

import rospy

from lula_ros.msg import JointPosVelAccCommand, LulaCommandAck


class CycleTime:
    def __init__(self, time, period=None):
        self.time = time
        self.period = period
        if period is None:
            self.is_period_available = False
        else:
            self.is_period_available = True


class SynchronizedTime:
    def __init__(self, skip_cycles=5):
        self.skip_cycles = skip_cycles
        self.cycle_count = 0

        self.sub = rospy.Subscriber("/rmpflow/commands/joint_command/ack", LulaCommandAck, self.callback)
        self.latest_message = LulaCommandAck()
        self.cycle_start_time = rospy.Time.now()
        self.current_offset = rospy.Duration(0)

    def __del__(self):
        self.sub.unregister()

    def callback(self, data):
        self.latest_message = data

    def next_adaptive_cycle_time(self):
        self.cycle_count += 1
        now = self.now_nonblocking()

        if self.cycle_count <= self.skip_cycles:
            ret = CycleTime(now)
        else:
            command_period = now - self.cycle_start_time
            ret = CycleTime(now, command_period)

            new_offset_measurement = self.latest_message.time_offset.to_sec()
            nominal_eps = math.pow(0.9999, 250.0)
            reg_decay = math.pow(nominal_eps, command_period.to_sec())
            ss = command_period.to_sec()
            self.current_offset = rospy.Duration(reg_decay * self.current_offset.to_sec() + ss * new_offset_measurement)

        self.cycle_start_time = now
        return ret

    def now_nonblocking(self):
        return rospy.Time.now() + self.current_offset
