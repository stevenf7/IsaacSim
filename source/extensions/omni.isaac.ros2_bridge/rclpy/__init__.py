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

import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self):
        ros_distro = os.environ.get("ROS_DISTRO")
        if ros_distro in ["humble", "foxy"] and f"{ros_distro}/rclpy" in os.path.join(os.path.dirname(__file__)):
            sys.path.append(os.path.join(os.path.dirname(__file__)))
            return

    def on_shutdown(self):
        sys.path.remove(os.path.join(os.path.dirname(__file__)))
