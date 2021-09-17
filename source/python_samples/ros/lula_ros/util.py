# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import sys

import rospy


def wait_for_connections(pubsub, stable_time=0.2, rate_hz=30):
    sys.stdout.write("waiting for connections to " + str(pubsub.name))
    sys.stdout.flush()
    rate = rospy.Rate(rate_hz)

    last_change_time = rospy.Time.now()
    num_con = pubsub.get_num_connections()
    while not rospy.is_shutdown():
        sys.stdout.write(".")
        sys.stdout.flush()
        curr_time = rospy.Time.now()

        latest_num_con = pubsub.get_num_connections()
        elapse_sec = (curr_time - last_change_time).to_sec()

        if latest_num_con != num_con:
            num_con = latest_num_con
            sys.stdout.write("%d" % num_con)
            sys.stdout.flush()
            last_change_time = curr_time
        elif elapse_sec >= stable_time:
            sys.stdout.write("<stable>\n")
            sys.stdout.flush()
            break
        rate.sleep()

    print("|<done>")
