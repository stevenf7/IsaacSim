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
