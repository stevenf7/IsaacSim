# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
from omni.isaac.ros_bridge import _ros_bridge


class RosBridgeUseSimTime(omni.kit.commands.Command):
    """
    Specify whether ROS bridge nodes publish their timestamp in sim time

    Args:
        arg0: (:obj:`bool`): `True` for sim time, `False` for system clock
    """

    def __init__(self, use_sim_time: bool):
        self._use_sim_time = use_sim_time
        self._ros_bridge = _ros_bridge.acquire_ros_bridge_interface()
        pass

    def do(self):
        self._ros_bridge.use_sim_time(self._use_sim_time)

    def undo(self):
        pass


class RosBridgeUsePhysicsStepSimTime(omni.kit.commands.Command):
    """
    Specify whether sim time is measured with physics steps or rendering/app updates

    Args:
        arg0: (:obj:`bool`): `True` for physics step, `False` for rendering step
    """

    def __init__(self, use_physics_step_sim_time: bool):
        self._use_physics_step_sim_time = use_physics_step_sim_time
        self._ros_bridge = _ros_bridge.acquire_ros_bridge_interface()
        pass

    def do(self):
        self._ros_bridge.use_physics_step_sim_time(self._use_physics_step_sim_time)

    def undo(self):
        pass


class RosBridgeTickComponent(omni.kit.commands.Command):
    """
    Tick all publishers/subscribers on a specific component

    Args:
        arg0: (:obj:`str`): Path to component

    Returns:

        `True` if component was found, `False` otherwise.
    """

    def __init__(self, path: str):
        self._path = path
        self._ros_bridge = _ros_bridge.acquire_ros_bridge_interface()
        pass

    def do(self):
        return self._ros_bridge.tick_component(self._path)

    def undo(self):
        pass


class RosBridgeRosMasterCheck(omni.kit.commands.Command):
    """
    Returns:

        `True` if ros master was found, `False` otherwise.
    """

    def __init__(self):
        self._ros_bridge = _ros_bridge.acquire_ros_bridge_interface()
        pass

    def do(self) -> bool:

        return self._ros_bridge.ros_master_check()

    def undo(self):
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
