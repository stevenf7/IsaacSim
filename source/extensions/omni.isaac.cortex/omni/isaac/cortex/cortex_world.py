# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.tasks.base_task import BaseTask

from omni.isaac.cortex.tools import SteadyRate


class LogicalStateMonitor:
    def __init__(self, name, logical_state):
        self.name = name
        self.logical_state = logical_state

    def pre_step(self):
        # Process the logical state monitors.
        for monitor in self.logical_state.monitors:
            monitor(self.logical_state)

    def post_reset(self):
        self.logical_state.reset()


class Behavior:
    """ Wrapper around a behavior for interfacing to a CortexWorld.

    A behavior can be any object that implements step() and reset().
    """

    def __init__(self, name, behavior):
        self.name = name
        self.behavior = behavior

    def pre_step(self):
        self.behavior.step()

    def post_reset(self):
        self.behavior.reset()


class CommandableArticulation(Articulation):
    """ A commandable articulation is an articulation with a collection of commanders controlling
    the joints. These commanders should be stepped through a call to step_commanders().
    """

    def step_commanders(self):
        raise NotImplementedError()

    def reset_commanders(self):
        raise NotImplementedError()

    def pre_step(self):
        self.step_commanders()

    def post_reset(self):
        super().post_reset()
        self.reset_commanders()


class CortexWorld(World):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logical_state_monitors = dict()
        self._behaviors = dict()
        self._robots = dict()

    def add_logical_state_monitor(self, ls_monitor: LogicalStateMonitor) -> None:
        self._logical_state_monitors[ls_monitor.name] = ls_monitor

    def add_behavior(self, behavior: Behavior) -> None:
        self._behaviors[behavior.name] = behavior

    def add_robot(self, robot: CommandableArticulation) -> CommandableArticulation:
        self._robots[robot.name] = robot
        self.scene.add(robot)
        return robot

    def step(self, render: bool = True, step_sim: bool = True) -> None:
        if self._task_scene_built:
            for task in self._current_tasks.values():
                task.pre_step(self.current_time_step_index, self.current_time)
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

        if self.scene._enable_bounding_box_computations:
            self.scene._bbox_cache.SetTime(Usd.TimeCode(self._current_time))

        if step_sim:
            SimulationContext.step(self, render=render)
        if self._data_logger.is_started():
            if self._data_logger._data_frame_logging_func is None:
                raise Exception("You need to add data logging function before starting the data logger")
            data = self._data_logger._data_frame_logging_func(tasks=self.get_current_tasks(), scene=self.scene)
            self._data_logger.add_data(
                data=data, current_time_step=self.current_time_step_index, current_time=self.current_time
            )
        return

    def reset(self, soft: bool = False) -> None:
        super().reset(soft)
        for ls_monitor in self._logical_state_monitors.values():
            ls_monitor.post_reset()
        for behavior in self._behaviors.values():
            behavior.post_reset()

    def step_loop_runner(self, simulation_app, render=True):
        physics_dt = self.get_physics_dt()
        rate_hz = 1.0 / physics_dt
        rate = SteadyRate(rate_hz)

        needs_reset = True  # Reset up front the first cycle through.
        while simulation_app.is_running():
            if self.is_playing():
                if needs_reset:
                    self.reset()
                    needs_reset = False
            elif self.is_stopped():
                # Every time the self steps playing we'll need to reset again when it starts again.
                needs_reset = True

            self.step(render=render)
            rate.sleep()
