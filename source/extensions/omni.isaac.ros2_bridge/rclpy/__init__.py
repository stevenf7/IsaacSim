# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import sys

import carb
import omni.ext
import omni.kit


class Extension(omni.ext.IExt):
    def on_startup(self):
        ros_distro = os.environ.get("ROS_DISTRO")
        if ros_distro in ["humble", "foxy"] and f"{ros_distro}/rclpy" in os.path.join(os.path.dirname(__file__)):
            omni.kit.app.get_app().print_and_log("Attempting to load system rclpy")
            try:
                import rclpy

                rclpy.init()
                omni.kit.app.get_app().print_and_log("rclpy loaded")
            except Exception as e:
                carb.log_warn(f"Could not import system rclpy: {e}")
                omni.kit.app.get_app().print_and_log("Attempting to load internal rclpy")
                sys.path.append(os.path.join(os.path.dirname(__file__)))
                try:
                    import rclpy

                    rclpy.init()
                    omni.kit.app.get_app().print_and_log("rclpy loaded")
                except Exception as e:
                    carb.log_warn(f"could not import internal rclpy: {e}")
            return

    def on_shutdown(self):
        rclpy_path = os.path.join(os.path.dirname(__file__))
        if rclpy_path in sys.path:
            sys.path.remove(rclpy_path)
