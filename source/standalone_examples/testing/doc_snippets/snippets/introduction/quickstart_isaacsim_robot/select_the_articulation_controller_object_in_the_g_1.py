# Get the number of joints
num_joints = arm_handle.num_joints
print("Number of joints: ", num_joints)

# Get joint names
joint_names = arm_handle.joint_names
print("Joint names: ", joint_names)

# Get joint limits
joint_limits = arm_handle.get_dof_limits()
print("Joint limits: ", joint_limits)

# Get joint positions
joint_positions = arm_handle.get_joint_positions()
print("Joint positions: ", joint_positions)
