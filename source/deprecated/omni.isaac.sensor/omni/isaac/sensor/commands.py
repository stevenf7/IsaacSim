# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni

old_extension_name = "omni.isaac.sensor"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name}.commands has been deprecated in favor of isaacsim.sensors.physics.commands, isaacsim.sensors.physx.commands, and isaacsim.sensors.rtx.commands. Please update your code accordingly."
)

from isaacsim.sensors.physics import IsaacSensorCreateContactSensor, IsaacSensorCreateImuSensor, IsaacSensorCreatePrim
from isaacsim.sensors.physx import IsaacSensorCreateLightBeamSensor
from isaacsim.sensors.rtx import IsaacSensorCreateRtxIDS, IsaacSensorCreateRtxLidar, IsaacSensorCreateRtxRadar
