# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb

old_extension_name = "omni.kit.property.isaac"
new_extension_name = "isaacsim.gui.property"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name}.widgets has been deprecated in favor of {new_extension_name}.widgets. Please update your code accordingly."
)
