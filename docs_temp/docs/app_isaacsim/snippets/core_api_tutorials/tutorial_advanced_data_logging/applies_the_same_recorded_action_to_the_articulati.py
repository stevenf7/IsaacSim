def _on_replay_scene_step(self, step_size):
    if self._world.current_time_step_index < self._data_logger.get_num_of_data_frames():
        target_name = self._task_params["target_name"]["value"]
        data_frame = self._data_logger.get_data_frame(data_frame_index=self._world.current_time_step_index)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=data_frame.data["applied_joint_positions"])
        )
        # Sets the world position of the goal cube to the same recorded position
        self._world.scene.get_object(target_name).set_world_pose(position=np.array(data_frame.data["target_position"]))
    return
