if self._policy_counter % self._decimation == 0:
    obs = self._compute_observation(command)
    self.action = self._compute_action(obs)
    self._previous_action = self.action.clone()

self.robot.set_dof_position_targets(positions=wp.from_torch(self.default_pos + (self.action * self._action_scale)))
self._policy_counter += 1
