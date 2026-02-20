# Move arm to a target pose. arm_handle from add_franka_to_stage snippet.
# Franka has 9 DOFs: 7 arm joints + 2 finger joints
arm_handle.set_dof_positions([-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04])

# To reset to default pose:
# arm_handle.set_dof_positions([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04, 0.04])
