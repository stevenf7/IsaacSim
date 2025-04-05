# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
SIMULATION_CONTEXT_ATTRIBUTES = ["gravity"]

RIGID_PRIM_ATTRIBUTES = [
    "angular_velocity",
    "linear_velocity",
    "velocity",
    "position",
    "orientation",
    "force",
    "mass",
    "inertia",
    "material_properties",
    "contact_offset",
    "rest_offset",
]

ARTICULATION_ATTRIBUTES = [
    "stiffness",
    "damping",
    "joint_friction",
    "position",
    "orientation",
    "linear_velocity",
    "angular_velocity",
    "velocity",
    "joint_positions",
    "joint_velocities",
    "lower_dof_limits",
    "upper_dof_limits",
    "max_efforts",
    "joint_armatures",
    "joint_max_velocities",
    "joint_efforts",
    "body_masses",
    "body_inertias",
    "material_properties",
    "contact_offset",
    "rest_offset",
    "tendon_stiffnesses",
    "tendon_dampings",
    "tendon_limit_stiffnesses",
    "tendon_lower_limits",
    "tendon_upper_limits",
    "tendon_rest_lengths",
    "tendon_offsets",
]

TENDON_ATTRIBUTES = [
    "tendon_stiffnesses",
    "tendon_dampings",
    "tendon_limit_stiffnesses",
    "tendon_lower_limits",
    "tendon_upper_limits",
    "tendon_rest_lengths",
    "tendon_offsets",
]
