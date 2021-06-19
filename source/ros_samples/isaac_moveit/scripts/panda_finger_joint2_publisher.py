#!/usr/bin/env python
import rospy
from sensor_msgs.msg import JointState

finger_joint2 = JointState()
finger_joint2.name = ["panda_finger_joint2"]


def joint_states_callback(message):
    for i, name in enumerate(message.name):
        if name == "panda_finger_joint1":
            pos = message.position[i]
            finger_joint2.position = [pos]
            pub.publish(finger_joint2)
    return


if __name__ == "__main__":
    rospy.init_node("panda_finger_joint2_publisher")
    pub = rospy.Publisher("/joint_command", JointState, queue_size=1)
    rospy.Subscriber("/joint_command", JointState, joint_states_callback, queue_size=1)
    rospy.spin()
