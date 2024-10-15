# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.isaac.benchmark.services"
new_extension_name = "isaacsim.benchmark.services"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name}.metrics.utils_metrics has been deprecated in favor of {new_extension_name}.metrics.utils_metrics. Please update your code accordingly."
)

from isaacsim.benchmark.services.metrics.utils_metrics import *
