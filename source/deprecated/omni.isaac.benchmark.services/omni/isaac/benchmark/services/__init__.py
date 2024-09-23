# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
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
    f"{new_extension_name} has been deprecated in favor of {old_extension_name}. Please update your code accordingly."
)

from .base_isaac_benchmark import *
from .base_isaac_benchmark_async import *
