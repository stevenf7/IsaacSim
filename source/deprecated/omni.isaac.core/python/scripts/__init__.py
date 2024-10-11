# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
from omni.isaac.core.physics_context.physics_context import PhysicsContext
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
from omni.isaac.core.world.world import World

old_extension_name = "omni.isaac.core"
new_extension_name = "isaacsim.core.api"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)
