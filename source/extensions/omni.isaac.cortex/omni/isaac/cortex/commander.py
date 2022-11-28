# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from abc import abstractmethod


class Commander:
    """ Abstract base class of a commander.

    A commander governs the control of a particular subset of joints. Users specify behavior by
    setting commands. The specific command API is left to the deriving class. The abstract API here
    is what's needed for this commander to be registerd with a ControlledArticulation object.

    Often, a deriving class would implement a set_command(self, command) method where command is a
    custom command type providing all the information needed for commanding the behavior. But we
    place no framework restrictions on how the command API is implemented. The methods below are
    what the framework needs in order to correctly process the commands and reset the commander when
    needed.

    This API is meant to model standard command APIs of robotic system. Often commands are sent
    through some pub-sub messaging system such as ZeroMQ or ROS and then processed from a real-time
    control loop. These real-time loops often tick once per cycle and process any queued message. In
    this case, we have synchronisity where commands might be set and the processed in the same step
    of the loop runner, so we can simplify implementations by assuming there will only be one
    command set per cycle (no queuing necessary). But we sparate out the command API calls (such as
    set_command(command)) from the processing of the commands to follow the commander model.
    """

    def __init__(self, articulation_subset):
        self.articulation_subset = articulation_subset
        self.latest_command = None

    @property
    def num_controlled_joints(self):
        return self.articulation_subset.num_joints

    @property
    def controlled_joints(self):
        return self.articulation_subset.joint_names

    @property
    def latest_action(self):
        return self.articulation_subset.get_applied_action()

    @property
    def command(self):
        return self.latest_command

    def send(self, command):
        self.latest_command = command

    def clear(self):
        self.latest_command = None

    @abstractmethod
    def step(self, dt):
        raise NotImplementedError()

    def reset(self):
        pass

    def post_reset(self):
        self.latest_command = None
        self.reset()
