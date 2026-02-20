current_joint_pos = self.get_joint_positions()
current_joint_vel = self.get_joint_velocities()

joint_torques, _ = self._actuator_network.compute_torques(
    current_joint_pos, current_joint_vel, self._action_scale * self.action
)

self.set_joint_efforts(joint_torques)
