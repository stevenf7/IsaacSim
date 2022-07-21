# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.replicator.core.scripts.utils import ReplicatorItem

from typing import Dict, List


def set_distribution_params(distribution: ReplicatorItem, parameters: Dict):
    node = distribution.node

    for parameter, value in parameters.items():
        attribute_name = "inputs:" + parameter

        if not node.get_attribute_exists(attribute_name):
            raise ValueError(f"This distribution does not have a parameter: `{parameter}`")

        node.get_attribute(attribute_name).set(value)


def get_distribution_params(distribution: ReplicatorItem, parameters: List[str]) -> List:
    node = distribution.node
    params = list()

    for parameter in parameters:
        attribute_name = "inputs:" + parameter

        if not node.get_attribute_exists(attribute_name):
            raise ValueError(f"This distribution does not have a parameter: `{parameter}`")

        value = node.get_attribute(attribute_name).get_array(
            on_gpu=False, get_for_write=False, reserved_element_count=0
        )

        params.append(value)

    return params
