# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from enum import Enum


class IsaacEvents(Enum):
    PHYSICS_WARMUP = "isaac.physics_warmup"
    SIMULATION_VIEW_CREATED = "isaac.simulation_view_created"
    PHYSICS_READY = "isaac.physics_ready"
    POST_RESET = "isaac.post_reset"
    PRIM_DELETION = "isaac.prim_deletion"
    PHYSICS_STEP = "isaac.physics_step"
    TIMELINE_STOP = "isaac.timeline_stop"
