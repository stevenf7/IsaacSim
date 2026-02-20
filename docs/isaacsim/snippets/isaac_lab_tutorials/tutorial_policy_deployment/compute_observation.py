obs = torch.zeros(69, device=torch.device(str(self.robot._device)))
# Base lin vel
obs[:3] = lin_vel_b.squeeze()
# Base ang vel
obs[3:6] = ang_vel_b.squeeze()
# Gravity
obs[6:9] = gravity_b.squeeze()
# Command
obs[9:12] = command
# Joint states
current_joint_pos = wp.to_torch(self.robot.get_dof_positions())
current_joint_vel = wp.to_torch(self.robot.get_dof_velocities())
obs[12:31] = current_joint_pos - self.default_pos
obs[31:50] = current_joint_vel - self.default_vel
# Previous Action
obs[50:69] = self._previous_action
