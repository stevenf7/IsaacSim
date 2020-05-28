import rospy
from sensor_msgs.msg import JointState
import numpy as np
import time


rospy.init_node("test_rosbridge", anonymous=True)

pub = rospy.Publisher("/joint_command", JointState, queue_size=10)
rate = rospy.Rate(20)
joint_state = JointState()

# for Franka Panda Robot
joint_state.name = [
    "panda_joint1",
    "panda_joint2",
    "panda_joint3",
    "panda_joint4",
    "panda_joint5",
    "panda_joint6",
    "panda_joint7",
    "panda_finger_joint1",
    "panda_finger_joint2",
]
num_joints = len(joint_state.name)
joint_state.position = np.array([0.0] * num_joints)
joint_state.velocity = [0.0] * num_joints
joint_state.effort = [0.0] * num_joints
default_joints = [0.0, -1.16, -0.0, -2.3, -0.0, 1.6, 1.1, 0.4, 0.4]

# limiting the movements to a smaller range (this is not the range of the robot, just the range of the movement
max_joints = np.array(default_joints) + 0.5
min_joints = np.array(default_joints) - 0.5

# position control the robot to wiggle around each joint
time_start = time.time()
while not rospy.is_shutdown():
    joint_state.position = np.sin(time.time() - time_start) * (max_joints - min_joints) * 0.5 + default_joints
    pub.publish(joint_state)
    rate.sleep()

# make sure kit's editor is playing for receiving messages
