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

carb.log_warn(
    "omni.isaac.benchmark.services.base_isaac_benchmark has been deprecated in favor of isaacsim.benchmark.services.base_isaac_benchmark. Please update your code accordingly."
)

from isaacsim.benchmark.services.base_isaac_benchmark import *
