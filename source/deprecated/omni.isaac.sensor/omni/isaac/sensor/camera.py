# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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
    f"{old_extension_name}.camera has been deprecated in favor of isaacsim.sensors.camera.camera. Please update your code accordingly."
)

from isaacsim.sensors.camera import (
    R_U_TRANSFORM,
    U_R_TRANSFORM,
    U_W_TRANSFORM,
    W_U_TRANSFORM,
    Camera,
    distort_point_kannala_brandt,
    distort_point_rational_polynomial,
    point_to_theta,
)
