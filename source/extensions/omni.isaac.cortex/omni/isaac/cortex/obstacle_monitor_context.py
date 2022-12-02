# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.cortex.df import DfLogicalState


class ObstacleMonitor:
    def __init__(self, context, obstacles):
        self.context = context
        self.obstacles = obstacles
        self.is_obstacles_enabled = True

    def is_obstacle_required(self):
        """ This is the main API method deriving classes should override.

        It should specify whethe this obstacle monitors obstacles are needed any any given time.
        It will be queried only when autotoggle is active.
        """
        raise NotImplementedError()

    def reset(self):
        self.is_autotoggle_active = False
        self.disable_obstacles()

    def activate_autotoggle(self):
        self.is_autotoggle_active = True

    def deactivate_autotoggle(self):
        self.is_autotoggle_active = False
        self.disable_obstacles_if_needed()

    def enable_obstacles(self):
        for obs in self.obstacles:
            self.context.robot.arm.enable_obstacle(obs)
        self.is_obstacles_enabled = True

    def enable_obstacles_if_needed(self):
        if not self.is_obstacles_enabled:
            self.enable_obstacles()

    def disable_obstacles(self):
        for obs in self.obstacles:
            self.context.robot.arm.disable_obstacle(obs)
        self.is_obstacles_enabled = False

    def disable_obstacles_if_needed(self):
        if self.is_obstacles_enabled:
            self.disable_obstacles()

    def step(self):
        if self.is_autotoggle_active:
            if self.is_obstacle_required():
                self.enable_obstacles_if_needed()
            else:
                self.disable_obstacles_if_needed()
        else:
            self.disable_obstacles_if_needed()


class ObstacleMonitorContext(DfLogicalState):
    def __init__(self):
        super().__init__()
        self.obstacle_monitors = []
        self.add_monitor(ObstacleMonitorContext.monitor_obstacles)

    def reset(self):
        for obs_monitor in self.obstacle_monitors:
            obs_monitor.reset()

    def add_obstacle_monitor(self, obstacle_monitor):
        self.obstacle_monitors.append(obstacle_monitors)

    def add_obstacle_monitors(self, obstacle_monitors):
        self.obstacle_monitors.extend(obstacle_monitors)

    def monitor_obstacles(self):
        for obs_monitor in self.obstacle_monitors:
            obs_monitor.step()
