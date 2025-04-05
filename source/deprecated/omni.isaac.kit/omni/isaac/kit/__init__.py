# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os
import sys

import carb

old_extension_name = "omni.isaac.kit"
new_extension_name = "isaacsim.simulation_app"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)

try:
    from isaacsim.simulation_app import AppFramework, SimulationApp
except ModuleNotFoundError:
    # resolve isaacsim.simulation_app extension path
    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path, "..", "..", "..", "..", "..", "exts", "isaacsim.simulation_app")
    sys.path.insert(0, os.path.abspath(path))

    from isaacsim.simulation_app import AppFramework, SimulationApp
