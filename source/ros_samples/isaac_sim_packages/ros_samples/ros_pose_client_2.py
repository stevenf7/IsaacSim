#!/usr/bin/env python

from __future__ import print_function

from isaac_ros_messages.srv import IsaacPose, IsaacPoseRequest
from geometry_msgs.msg import Pose, Twist, Vector3
import rospy
import numpy as np


def send_pose_cone_client(new_pose):
    rospy.wait_for_service("/teleport_pos_cone")
    try:
        send_pose = rospy.ServiceProxy("/teleport_pos_cone", IsaacPose)
        send_pose(new_pose)

    except rospy.ServiceException as e:
        print("Service call failed: %s" % e)


def compose_pose(pos_vec, quat_vec):
    obj_pose = Pose()
    obj_pose.position.x = pos_vec[0]
    obj_pose.position.y = pos_vec[1]
    obj_pose.position.z = pos_vec[2]
    obj_pose.orientation.w = quat_vec[0]
    obj_pose.orientation.x = quat_vec[1]
    obj_pose.orientation.y = quat_vec[2]
    obj_pose.orientation.z = quat_vec[3]
    return obj_pose


def compose_twist(lx, ly, lz, ax, ay, az):
    obj_twist = Twist()
    obj_twist.linear.x = lx
    obj_twist.linear.y = ly
    obj_twist.linear.z = lz
    obj_twist.angular.x = ax
    obj_twist.angular.y = ay
    obj_twist.angular.z = az
    return obj_twist


def compose_vec3(x, y, z):
    obj_scale = Vector3()
    obj_scale.x = x
    obj_scale.y = y
    obj_scale.z = z
    return obj_scale


if __name__ == "__main__":
    rospy.init_node("test_ros_teleport_cone", anonymous=True)
    new_isaac_pose_cone = IsaacPoseRequest()
    new_isaac_pose_cone.names = ["/Cone"]

    cone_pos_vec = np.array([0.0, 0.0, 0.0])
    quat_vec = np.array([1, 0.0, 0.0, 0.0])

    rate = rospy.Rate(2)  # hz

    while not rospy.is_shutdown():
        # new pose
        cone_pos_vec += 0.02
        cone_pose = compose_pose(cone_pos_vec, [0, 0.707, 0.707, 0])
        new_isaac_pose_cone.poses = [cone_pose]

        # new twist
        zero_twist = compose_twist(0, 0, 0, 0, 0, 0)
        new_isaac_pose_cone.velocities = [zero_twist]
        # new scale
        unit_scale = compose_vec3(1, 1, 1)
        new_isaac_pose_cone.scales = [unit_scale]
        # publish
        send_pose_cone_client(new_isaac_pose_cone)
        rate.sleep()
