# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
from omni.isaac.ros2_bridge import _ros2_bridge


class Ros2BridgeUseSimTime(omni.kit.commands.Command):
    """
    Specify whether ROS2 bridge nodes publish their timestamp in sim time

    Args:
        arg0: (:obj:`bool`): `True` for sim time, `False` for system clock
    """

    def __init__(self, use_sim_time: bool):
        self._use_sim_time = use_sim_time
        self._ros2_bridge = _ros2_bridge.acquire_ros2_bridge_interface()
        pass

    def do(self):
        self._ros2_bridge.use_sim_time(self._use_sim_time)

    def undo(self):
        pass


class Ros2BridgeTickComponent(omni.kit.commands.Command):
    """
    Tick all publishers/subscribers on a specific component

    Args:
        arg0: (:obj:`str`): Path to component

    Returns:

        `True` if component was found, `False` otherwise.
    """

    def __init__(self, path: str):
        self._path = path
        self._ros2_bridge = _ros2_bridge.acquire_ros2_bridge_interface()
        pass

    def do(self):
        return self._ros2_bridge.tick_component(self._path)

    def undo(self):
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
