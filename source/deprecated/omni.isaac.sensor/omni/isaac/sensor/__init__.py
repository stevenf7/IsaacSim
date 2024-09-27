# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.isaac.sensor"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of isaacsim.sensors.camera, isaacsim.sensors.physics, isaacsim.sensors.physx, and isaacsim.sensors.rtx. Please update your code accordingly."
)

from .camera import *
from .camera_view import CameraView
from .commands import *
from .contact_sensor import ContactSensor
from .imu_sensor import IMUSensor
from .lidar_rtx import LidarRtx
from .rotating_lidar_physX import RotatingLidarPhysX
