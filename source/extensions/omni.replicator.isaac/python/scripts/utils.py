# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.replicator.core.scripts.utils import ReplicatorItem
from typing import Dict, List


def set_distribution_params(distribution: ReplicatorItem, parameters: Dict) -> None:
    """ 
        Args:
            distribution (ReplicatorItem): The replicator distribution object to be modified.
            parameters (Dict): A dictionary where the keys are the names of the replicator 
                               distribution parameters and the values are the parameter values 
                               to be set.
    """
    node = distribution.node

    for parameter, value in parameters.items():
        attribute_name = "inputs:" + parameter
        if not node.get_attribute_exists(attribute_name):
            raise ValueError(f"This distribution does not have a parameter: `{parameter}`")
        node.get_attribute(attribute_name).set(value)


def get_distribution_params(distribution: ReplicatorItem, parameters: List[str]) -> List:
    """ 
        Args:
            distribution (ReplicatorItem): A replicator distribution object.
            parameters (List[str]): A list of the names of the replicator distribution parameters.
        Returns:
            List[str]: A list of the distribution parameters of the given replicator distribution object.

    """
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
