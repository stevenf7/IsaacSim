joint_state = JointState()
joint_state.name = ["joint1", "joint2", "joint3", "wheel_left_joint", "wheel_right_joint"]
joint_state.position = [0.2, 0.2, 0.2, float("nan"), float("nan")]
joint_state.velocity = [float("nan"), float("nan"), float("nan"), 20.0, -20.0]
