# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.isaac.range_sensor"
new_extension_name = "isaacsim.sensors.physx"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name}.commands has been deprecated in favor of {new_extension_name}.commands. Please update your code accordingly."
)

from isaacsim.sensors.physx import (
    RangeSensorCreateGeneric,
    RangeSensorCreateLidar,
    RangeSensorCreatePrim,
    RangeSensorCreateUltrasonicArray,
    RangeSensorCreateUltrasonicEmitter,
    RangeSensorCreateUltrasonicFiringGroup,
)
