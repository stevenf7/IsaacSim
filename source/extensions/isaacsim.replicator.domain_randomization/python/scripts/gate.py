# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from omni.replicator.core.utils import ReplicatorItem, ReplicatorWrapper, create_node


@ReplicatorWrapper
def on_interval(interval):
    """
    Args:
        interval (int): The frequency interval for randomization. The interval is incremented
                        by isaacsim.replicator.domain_randomization.physics_view.step_randomization() call.
    """
    node = create_node("isaacsim.replicator.domain_randomization.OgnIntervalFiltering")
    trigger_node = ReplicatorItem._get_context()

    node.get_attribute("inputs:interval").set(interval)
    trigger_node.get_attribute("outputs:execOut").connect(node.get_attribute("inputs:execIn"), True)
    trigger_node.get_attribute("outputs:frameNum").connect(node.get_attribute("inputs:frameCounts"), True)

    return node


@ReplicatorWrapper
def on_env_reset():
    node = create_node("isaacsim.replicator.domain_randomization.OgnIntervalFiltering")
    trigger_node = ReplicatorItem._get_context()

    node.get_attribute("inputs:ignoreInterval").set(True)
    trigger_node.get_attribute("outputs:execOut").connect(node.get_attribute("inputs:execIn"), True)
    trigger_node.get_attribute("outputs:resetInds").connect(node.get_attribute("inputs:indices"), True)

    return node
