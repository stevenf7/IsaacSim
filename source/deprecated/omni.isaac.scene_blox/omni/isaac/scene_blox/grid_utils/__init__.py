# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb

old_extension_name = "omni.isaac.scene_blox"
new_extension_name = "isaacsim.replicator.scene_blox"
module_name = "grid_utils"

carb.log_warn(
    f"{old_extension_name}.{module_name} has been deprecated in favor of {new_extension_name}.{module_name}. Please update your code accordingly."
)
