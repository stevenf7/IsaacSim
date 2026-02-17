self.gripper_interface = surface_gripper.acquire_surface_gripper_interface()
status = self.gripper_interface.get_gripper_status(self.gripper_prim_path)
print(status)  # Open, Closed, or Closing
