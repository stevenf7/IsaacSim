async def _on_replay_trajectory_event_async(self, data_file):
    # Loads the data from the json file
    self._data_logger.load(log_path=data_file)
    world = self.get_world()
    await world.play_async()
    # Adds the physics callback to set the joint targets every frame
    world.add_physics_callback("replay_trajectory", self._on_replay_trajectory_step)
    return


def _on_replay_trajectory_step(self, step_size):
    if self._world.current_time_step_index < self._data_logger.get_num_of_data_frames():
        # To sync time steps and get the data frame at the same time step
        data_frame = self._data_logger.get_data_frame(data_frame_index=self._world.current_time_step_index)
        # Applies the same recorded action to the articulation controller
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=data_frame.data["applied_joint_positions"])
        )
    return
