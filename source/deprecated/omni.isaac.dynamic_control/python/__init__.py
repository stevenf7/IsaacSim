# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

from .scripts import *

extension_name = "omni.isaac.dynamic_control"

# Provide deprecation warning to user
carb.log_warn(f"{extension_name} is deprecated as of Isaac Sim 4.5. No action is needed from end-users.")
