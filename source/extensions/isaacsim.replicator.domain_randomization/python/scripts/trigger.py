# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from omni.replicator.core.utils import ReplicatorWrapper, create_node

from .context import initialize_context


@ReplicatorWrapper
def on_rl_frame(num_envs: int):
    """
    Args:
        num_envs (int): The number of environments corresponding to the number of prims
                        encapsulated in the RigidPrimViews and ArticulationViews.
    """
    node = create_node("isaacsim.replicator.domain_randomization.OgnOnRLFrame")
    node.get_attribute("inputs:num_envs").set(num_envs)

    initialize_context(num_envs, node)

    return node
