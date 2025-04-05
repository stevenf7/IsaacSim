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

old_extension_name = "omni.isaac.motion_generation"
new_extension_name = "isaacsim.robot_motion.motion_generation"


# Provide deprecation warning to user

carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)


from .articulation_kinematics_solver import *
from .articulation_motion_policy import *
from .articulation_trajectory import *
from .kinematics_interface import *
from .lula.kinematics import *
from .lula.motion_policies import *
from .lula.trajectory_generator import *
from .motion_policy_controller import *
from .motion_policy_interface import *
from .path_planner_visualizer import *
from .path_planning_interface import *
from .trajectory import *
from .world_interface import *
