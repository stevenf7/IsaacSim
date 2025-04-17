# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from enum import Enum


class IsaacEvents(Enum):
    PHYSICS_WARMUP = "isaac.physics_warmup"
    SIMULATION_VIEW_CREATED = "isaac.simulation_view_created"
    PHYSICS_READY = "isaac.physics_ready"
    POST_RESET = "isaac.post_reset"
    PRIM_DELETION = "isaac.prim_deletion"
    PRE_PHYSICS_STEP = "isaac.pre_physics_step"
    POST_PHYSICS_STEP = "isaac.post_physics_step"
    TIMELINE_STOP = "isaac.timeline_stop"
