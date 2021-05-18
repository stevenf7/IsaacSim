import os
import omni.ext

from .. import _ros2_bridge
import carb


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # self._rosbridge = None
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros_bridge"):
            carb.log_error("ROS Bridge extension cannot be enabled if ROS Bridge is enabled")
            ext_manager.set_extension_enabled("omni.isaac.ros2_bridge", False)
            return

        # print("Checking if ROS_MASTER_URI is set: ")
        # if "ROS_MASTER_URI" in os.environ:
        #     print("Found ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])
        # else:
        #     os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
        #     print("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])

        # ROS2 uses LD_LIBRARY_PATH to load libraries at runtime so set it here before the plugin loads.
        self._extension_path = ext_manager.get_extension_path(ext_id)
        os.environ["LD_LIBRARY_PATH"] = self._extension_path + "/bin"

        self._ros2bridge = _ros2_bridge.acquire_ros2_bridge_interface()

    def on_shutdown(self):
        if self._ros2bridge is not None:
            _ros2_bridge.release_ros2_bridge_interface(self._ros2_bridge)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros_bridge") is False:
            ext_manager.set_extension_enabled("omni.isaac.ros_ui", False)
            return
