# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# Copyright(c) 2021-2022, NVIDIA CORPORATION.All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb

carb.log_warn(
    "omni.isaac.core.articulations.articulation_subset has been deprecated in favor of isaacsim.core.api.articulations.articulation_subset. Please update your code accordingly."
)

from isaacsim.core.api.articulations.articulation_subset import ArticulationSubset, require_initialized
