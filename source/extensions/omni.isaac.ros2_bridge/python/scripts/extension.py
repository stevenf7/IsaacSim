# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import omni.ext

from .. import _ros2_bridge
import carb


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._ros2bridge = None
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros_bridge"):
            carb.log_error("ROS 2 Bridge extension cannot be enabled if ROS Bridge is enabled")
            ext_manager.set_extension_enabled("omni.isaac.ros2_bridge", False)
            return

        # ROS2 uses LD_LIBRARY_PATH to load libraries at runtime so set it here before the plugin loads.
        self._extension_path = ext_manager.get_extension_path(ext_id)
        os.environ["LD_LIBRARY_PATH"] = self._extension_path + "/bin"

        self._ros2bridge = _ros2_bridge.acquire_ros2_bridge_interface()

    def on_shutdown(self):
        if self._ros2bridge is not None:
            _ros2_bridge.release_ros2_bridge_interface(self._ros2bridge)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled("omni.isaac.ros_bridge") is False:
            ext_manager.set_extension_enabled("omni.isaac.ros_bridge_ui", False)
            return
