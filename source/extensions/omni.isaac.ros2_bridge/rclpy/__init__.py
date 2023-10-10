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
    def on_startup(self, ext_id):
        ros_distro = os.environ.get("ROS_DISTRO")
        if ros_distro in ["humble", "foxy"] and f"{ros_distro}/rclpy" in os.path.join(os.path.dirname(__file__)):
            omni.kit.app.get_app().print_and_log("Attempting to load system rclpy")
            ament_prefix = os.environ.get("AMENT_PREFIX_PATH")
            if ament_prefix is not None and os.environ.get("OLD_PYTHONPATH") is not None:
                for python_path in os.environ.get("OLD_PYTHONPATH").split(":"):
                    for ament_path in ament_prefix.split(":"):
                        if python_path.startswith(os.path.abspath(ament_path) + os.sep):
                            sys.path.append(os.path.join(python_path))
                            break
            try:
                import rclpy

                rclpy.init()
                rclpy.shutdown()
                omni.kit.app.get_app().print_and_log("rclpy loaded")
            except Exception as e:
                omni.kit.app.get_app().print_and_log(f"Could not import system rclpy: {e}")
                omni.kit.app.get_app().print_and_log("Attempting to load internal rclpy")
                sys.path.append(os.path.join(os.path.dirname(__file__)))
                ext_manager = omni.kit.app.get_app().get_extension_manager()
                self._extension_path = ext_manager.get_extension_path(ext_id)
                if sys.platform == "win32":
                    if os.environ.get("PATH"):
                        os.environ["PATH"] = os.environ.get("PATH") + ";" + self._extension_path + f"/{ros_distro}/lib"
                    else:
                        os.environ["PATH"] = self._extension_path + f"/{ros_distro}/lib"
                        os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"
                try:
                    import rclpy

                    rclpy.init()
                    rclpy.shutdown()
                    omni.kit.app.get_app().print_and_log("rclpy loaded")
                except Exception as e:
                    omni.kit.app.get_app().print_and_log(f"Could not import internal rclpy: {e}")
                    if sys.platform == "linux":
                        omni.kit.app.get_app().print_and_log(
                            f"To use the internal libraries included with the extension please set: \nRMW_IMPLEMENTATION=rmw_fastrtps_cpp\nLD_LIBRARY_PATH=$LD_LIBRARY_PATH:{self._extension_path}/{ros_distro}/lib\nBefore starting Isaac Sim"
                        )
                    else:
                        omni.kit.app.get_app().print_and_log(
                            f"To use the internal libraries included with the extension please set: \nRMW_IMPLEMENTATION=rmw_fastrtps_cpp\nPATH=%PATH%;{self._extension_path}/{ros_distro}/lib\nBefore starting Isaac Sim"
                        )
                try:
                    import rclpy

                    rclpy.init()
                    rclpy.shutdown()
                except Exception as e:
                    carb.log_warn("Could not import rclpy")
                    carb.log_warn(
                        "Omnigraph nodes cannot publish/subscribe and rlclpy and related imports will not be available."
                    )
            return

    def on_shutdown(self):
        rclpy_path = os.path.join(os.path.dirname(__file__))
        if rclpy_path in sys.path:
            sys.path.remove(rclpy_path)
