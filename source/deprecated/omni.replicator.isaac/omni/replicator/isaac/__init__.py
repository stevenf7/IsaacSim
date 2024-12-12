# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.replicator.isaac"
new_extension_name = (
    "isaacsim.replicator.domain_randomization, isaacsim.replicator.examples, isaacsim.replicator.writers"
)

carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)

from isaacsim.replicator.domain_randomization.scripts import context, gate, physics_view, trigger, utils
from isaacsim.replicator.domain_randomization.scripts.attributes import (
    ARTICULATION_ATTRIBUTES,
    RIGID_PRIM_ATTRIBUTES,
    SIMULATION_CONTEXT_ATTRIBUTES,
    TENDON_ATTRIBUTES,
)
