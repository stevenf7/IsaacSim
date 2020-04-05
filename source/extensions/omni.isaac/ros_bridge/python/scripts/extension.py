import os
import omni.kit.extensions
from ..bindings import _ros_bridge
from .ros_menu import RosBridgeMenu


class Extension:
    def on_startup(self):
        print("Checking if ROS_MASTER_URI is set: ")
        if "ROS_MASTER_URI" in os.environ:
            print("Found ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])
        else:
            os.environ["ROS_MASTER_URI"] = "http://localhost:11311"
            print("ROS_MASTER_URI not set, using default, ROS_MASTER_URI=", os.environ["ROS_MASTER_URI"])

        ext_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        lib_path = omni.kit.extensions.build_plugin_path(ext_folder, "omni.isaac.ros_bridge.plugin")

        print("Loading RosBridge interface from ", lib_path)
        self._rosbridge = _ros_bridge.acquire_rosbridge_interface(library_path=lib_path)
        self._ros_menu = RosBridgeMenu(self._rosbridge)

    def on_shutdown(self):
        _ros_bridge.release_rosbridge_interface(self._rosbridge)
        self._ros_menu.shutdown()
        self._ros_menu = None

    def get_deps(self):
        return "omni.physx,omni.isaac.dynamic_control"


def get_extension():
    return Extension()
