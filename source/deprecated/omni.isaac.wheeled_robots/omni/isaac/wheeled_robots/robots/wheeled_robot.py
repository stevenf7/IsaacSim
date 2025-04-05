# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
    "omni.isaac.wheeled_robots has been deprecated in favor of isaacsim.robot.wheeled_robots. Please update your code accordingly."
)

from isaacsim.robot.wheeled_robots.robots.wheeled_robot import *
