def step(self, render: bool = True, step_sim: bool = True) -> None:
    if self._task_scene_built:
        ...
        if self.is_playing():
            # Cortex pipeline: Process logical state monitors, then make decisions based on that
            # logical state (sends commands to the robot's commanders), and finally step the
            # robot's commanders to handle those commands.
            for ls_monitor in self._logical_state_monitors.values():
                ls_monitor.pre_step()
            for behavior in self._behaviors.values():
                behavior.pre_step()
            for robot in self._robots.values():
                robot.pre_step()
        ...
