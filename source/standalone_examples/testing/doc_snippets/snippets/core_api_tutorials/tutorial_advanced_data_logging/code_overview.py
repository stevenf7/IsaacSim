def _on_logging_event(self, val):
    world = self.get_world()
    data_logger = world.get_data_logger()  # a DataLogger object is defined in the World by default
    if not world.get_data_logger().is_started():
        robot_name = self._task_params["robot_name"]["value"]
        target_name = self._task_params["target_name"]["value"]

        # A data logging function is called at every time step index if the data logger is started already.
        # We define the function here. The tasks and scene are passed to this function when called.

        def frame_logging_func(tasks, scene):
            return {
                "joint_positions": scene.get_object(robot_name)
                .get_joint_positions()
                .tolist(),  # save data as lists since its a JSON file.
                "applied_joint_positions": scene.get_object(robot_name).get_applied_action().joint_positions.tolist(),
                "target_position": scene.get_object(target_name).get_world_pose()[0].tolist(),
            }

        data_logger.add_data_frame_logging_func(
            frame_logging_func
        )  # adds the function to be called at each physics time step.
    if val:
        data_logger.start()  # starts the data logging
    else:
        data_logger.pause()
    return
