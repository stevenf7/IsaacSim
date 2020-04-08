import os
import omni.ext
from .. import _ros_bridge
from .ros_menu import RosBridgeMenu


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Checking if ROS_MASTER_URI is set: ")
        if "ROS_MASTER_URI" in os.environ:
            print("Found ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])
        else:
            os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
            print("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])

        print("Loading RosBridge interface")
        self._rosbridge = _ros_bridge.acquire_rosbridge_interface()
        self._ros_menu = RosBridgeMenu(self._rosbridge)

    def on_shutdown(self):
        _ros_bridge.release_rosbridge_interface(self._rosbridge)
        self._ros_menu.shutdown()
        self._ros_menu = None
