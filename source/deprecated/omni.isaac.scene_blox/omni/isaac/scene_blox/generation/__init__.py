# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.isaac.scene_blox"
new_extension_name = "isaacsim.replicator.scene_blox"
module_name = "generation"

carb.log_warn(
    f"{old_extension_name}.{module_name} has been deprecated in favor of {new_extension_name}.{module_name}. Please update your code accordingly."
)
