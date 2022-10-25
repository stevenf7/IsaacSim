# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from omni.isaac.core import World
from omni.isaac.core.tasks.base_task import BaseTask

from omni.isaac.cortex.cortex_utils import make_motion_commander


class CortexTask(BaseTask):
    def __init__(self, name, robot, target_prim, obstacles):
        """ Behaviors are specified by the behavior_builder which is called on reset to build the behavior.
        A ContextTools(robot, commander, obstacles) object is passed into it as the tools object. Those
        tools are then available to the behavior along with the World singleton.
        """
        super().__init__(name)
        self.robot = robot
        self.target_prim = target_prim
        self.obstacles = obstacles

    def build_behavior(self, tools):
        raise NotImplementedError()

    def pre_step(self, time_step_index: int, simulation_time: float):
        if World.instance().is_playing():
            self.tick_behavior()

    def tick_behavior(self):
        self.behavior.tick()  # The behavior tick sets the command of the motion commander.
        self.commander.get_and_apply_action()

    def post_reset(self):
        self.commander = make_motion_commander(World.instance().get_physics_dt(), self.robot, self.target_prim)
        self.behavior = self.build_behavior(CortexTools(self.robot, self.commander, self.obstacles))


class CortexTools:
    """ The tools passed in to a behavior when build_behavior(tools) is called.

    Other objects in the environment can be accessed from the world singleton from inside the
    behavior (e.g. from the context constructor).
    """

    def __init__(self, robot, commander, obstacles):
        self.robot = robot
        self.commander = commander
        self.obstacles = obstacles
