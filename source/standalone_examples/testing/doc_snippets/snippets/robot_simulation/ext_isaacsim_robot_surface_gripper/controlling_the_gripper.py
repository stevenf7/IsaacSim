self.gripper_interface.close_gripper(gripper_prim_path)

self.gripper_interface.open_gripper(gripper_prim_path)

self.gripper_interface.set_gripper_action(gripper_prim_path, 0.5)  # Closes the gripper
self.gripper_interface.set_gripper_action(gripper_prim_path, -0.5)  # Opens the gripper
