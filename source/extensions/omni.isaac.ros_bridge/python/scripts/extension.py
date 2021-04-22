import os
import omni.ext
from .. import _ros_bridge
from .menu import RosBridgeMenu
from .roscore import Roscore


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Checking if ROS_MASTER_URI is set: ")
        if "ROS_MASTER_URI" in os.environ:
            print("Found ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])
        else:
            os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
            print("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])

        self._rosbridge = _ros_bridge.acquire_rosbridge_interface()
        self._menu = RosBridgeMenu()
        # self._roscore = Roscore()
        # self._roscore.startup()

    def on_shutdown(self):
        _ros_bridge.release_rosbridge_interface(self._rosbridge)
        self._menu.shutdown()
        self._menu = None
        # self._roscore.shutdown()
