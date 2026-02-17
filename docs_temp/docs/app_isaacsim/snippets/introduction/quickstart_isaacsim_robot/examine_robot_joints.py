# Requires physics running (Press Play first). arm_handle from add_franka_to_stage snippet.
print("Number of joints:", arm_handle.num_dofs)
print("Joint names:", arm_handle.dof_names)
positions = arm_handle.get_dof_positions()
print("Joint positions:", positions)
