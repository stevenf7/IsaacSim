# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

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
