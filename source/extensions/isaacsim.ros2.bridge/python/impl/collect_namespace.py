# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Dict, Tuple

import carb
import cv2 as cv
import numpy as np
import omni
import omni.syntheticdata
from isaacsim.core.utils.render_product import get_camera_prim_path
from pxr import Gf, Sdf, Usd


def collect_namespace(namespace_input: str, render_product_path: str) -> str:
    """
    If no input namespace is undefined, this method collects the namespace from a USD Prim by traversing its hierarchy upwards, and appends any 'isaac:namespace' attributes found.

    Parameters:
    - namespace_input: A string representing an initial namespace. If this is non-empty, it will be returned as-is.
    - render_product_path: A string representing the path of the render product, used to find the Camera prim associated with the render product.


    Returns:
    - A string representing the accumulated namespace.
    """

    # If the namespace_input is not empty, return it immediately
    if namespace_input:
        return namespace_input

    if not render_product_path:
        return ""

    namespace_string = ""

    start_prim_path = get_camera_prim_path(render_product_path)

    stage = omni.usd.get_context().get_stage()
    start_prim = stage.GetPrimAtPath(start_prim_path)

    current_prim = start_prim

    # Traverse upwards until there are no more parents
    while current_prim.IsValid():

        # Retrieve the "isaac:namespace" attribute
        attr = current_prim.GetAttribute("isaac:namespace")
        namespace_value = ""

        # If the attribute has a value, append it to the namespace string
        if attr:
            namespace_value = attr.Get()
            if namespace_value:
                if namespace_string:
                    namespace_string = namespace_value + "/" + namespace_string
                else:
                    namespace_string = namespace_value

        # Move to the parent prim
        current_prim = current_prim.GetParent()

    return namespace_string
