# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import List

# Name of GXF bridge extension
GXF_BRIDGE_EXTENSION_NAME = "omni.isaac.gxf_bridge"

# GXF YAML files specifying simple graphs
DEFAULT_ATLAS_YAML = "default_atlas.yaml"
DEFAULT_CLOCK_YAML = "default_clock.yaml"
DEFAULT_ALLOCATOR_YAML = "isaac_sim_allocator.yaml"

# Asset and prim paths for GXF robot assets
ROBOT_ASSET_PATHS = {"carter_v2_3": "/Isaac/Samples/Isaac_AMR/Robots/carter_v2_3_gxf.usd"}
ROBOT_PRIM_PATHS = {"carter_v2_3": "/carter_v2_3"}


def set_yaml_addr_port(yaml: List[dict], address: str, port: int) -> bool:
    """Sets TCP server port & address in provided YAML documents.

    Args:
        yaml(List[dict]): List of dictionaries representing YAML documents.
        address (str): address to set server to.
        port (str): port to set server to.

    Returns:
        bool: True if successful; False otherwise.
    """
    for entity in yaml:
        if entity is None:
            continue
        for component in entity["components"]:
            if component["type"] == "nvidia::gxf::TcpServer":
                component["parameters"]["address"] = address
                component["parameters"]["port"] = port
                return True
    return False
