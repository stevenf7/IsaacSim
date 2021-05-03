import os
import omni.ext
from .. import _ros_bridge
import carb


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._rosbridge = None
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros2_bridge"):
            carb.log_error("ROS Bridge extension cannot be enabled if ROS 2 Bridge is enabled")
            ext_manager.set_extension_enabled("omni.isaac.ros_bridge", False)
            return

        print("Checking if ROS_MASTER_URI is set: ")
        if "ROS_MASTER_URI" in os.environ:
            print("Found ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])
        else:
            os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
            print("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])

        self._rosbridge = _ros_bridge.acquire_rosbridge_interface()

    def on_shutdown(self):
        if self._rosbridge is not None:
            _ros_bridge.release_rosbridge_interface(self._rosbridge)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros2_bridge") is False:
            ext_manager.set_extension_enabled("omni.isaac.ros_ui", False)
            return
