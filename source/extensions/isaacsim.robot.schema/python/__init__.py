# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os

import carb.tokens
from pxr import Plug


def _register_plugin_path(path):
    result = Plug.Registry().RegisterPlugins(path)
    if not result:
        import carb

        carb.log_error(f"No plugins found at path {path}")


def _register_plugins(ext_path: str):
    _register_plugin_path(os.path.join(ext_path, "usd", "schema", "isaac", "robot_schema"))

    plugin_path = os.path.join(ext_path, "plugins", "plugins")
    _register_plugin_path(os.path.join(plugin_path, "isaacSensorSchema", "resources"))
    _register_plugin_path(os.path.join(plugin_path, "rangeSensorSchema", "resources"))


_register_plugins(carb.tokens.get_tokens_interface().resolve("${isaacsim.robot.schema}"))


from . import robot_schema
