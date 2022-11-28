# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from abc import abstractmethod
import numpy as np

from omni.isaac.core import World
from omni.isaac.core.tasks.base_task import BaseTask


# class CortexTask(BaseTask):
#    def __init__(self, name, context):
#        super().__init__(name)
#        self.context = context
#
#    #def build_behavior(self):
#    #    raise NotImplementedError()
#
#    def pre_step(self, time_step_index: int, simulation_time: float):
#        #if World.instance().is_playing():
#        self.context.process_monitors()
#        #self.step_behavior()
#
#    #def step_behavior(self):
#    #    self.behavior.step()  # The behavior tick sets the command of the motion commander.
#    #    self.robot.step_commanders()
#
#    def post_reset(self):
#        self.context.reset()
#
